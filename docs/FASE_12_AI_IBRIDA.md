# FASE 12 — AI Conversazionale Ibrida (Ollama + Cloud)

## 1. Architettura

L'architettura estende il Voice Bridge FastAPI esistente senza modificare il firmware ESP32-S3 (`jarvis_wifi_voice_client`), il protocollo WSS v1.0, Whisper `small/int8` o Piper TTS:

```text
ESP32-S3 (GPIO47, INMP441, MAX98357A)
   │  WSS/TLS (PCM16 16kHz mono)
   ▼
VoiceBridgeService (pipeline.py)
   ├─► FasterWhisperEngine (small / int8)
   ├─► BridgeConversationContext (sessione in-memory, anti-injection)
   ├─► LocalIntentHandler (Priorità 0: ora, giorno, data, reset contesto)
   ├─► AIRouter (ai_router.py)
   │      ├─ Mode: DISABLED | LOCAL_ONLY | CLOUD_ONLY | LOCAL_FIRST | CLOUD_FIRST
   │      ├─ OllamaRouterClient (127.0.0.1:11434, solo locale)
   │      ├─ CloudAIClient (OpenAI-compatible HTTPS, limiti uso/costi)
   │      └─ OfflineFallbackProvider (messaggio vocale chiaro in italiano)
   └─► PiperTTSEngine (troncamento pulito <= tts_max_chars)
```

## 2. Moduli coinvolti

- `05-Voice-AI/voice_bridge/config.py`: caricamento variabili `JARVIS_AI_*`, `JARVIS_OLLAMA_*`, `JARVIS_CLOUD_*`, `JARVIS_CONVERSATION_*`, `JARVIS_TTS_MAX_CHARS`, con default sicuro `JARVIS_AI_MODE=DISABLED`.
- `05-Voice-AI/voice_bridge/security.py`: aggiunta `validate_cloud_url()` (HTTPS obbligatorio + blocco IP privati/loopback/link-local anti-SSRF).
- `05-Voice-AI/voice_bridge/conversation.py`: `BridgeConversationContext` con limiti configurabili di messaggi e token, sanitizzazione marker di role-spoofing/prompt-injection e `truncate_for_tts()`.
- `05-Voice-AI/voice_bridge/ai_router.py`: `OllamaRouterClient`, `CloudAIClient`, `AIRouter` con 5 modalità, fallback condizionato da `JARVIS_AI_FALLBACK_ENABLED`, budget di timeout complessivo `ai_timeout_s` e supporto cancellazione.
- `05-Voice-AI/voice_bridge/pipeline.py`: integrazione `cancel_check`, `tts_max_chars`, registrazione turni in memoria solo per risposte AI reali, reset vocale e API `reset_conversation()`.
- `05-Voice-AI/voice_bridge/api.py`: endpoint autenticato `POST /api/v1/conversation/reset`.
- `05-Voice-AI/voice_bridge/.env.bridge.example`: parametri documentati senza segreti.
- `05-Voice-AI/tests/test_hybrid_ai_fase12.py`: suite isolata e simulata da 16 test.

## 3. Provider

### Ollama Locale (`OllamaRouterClient`)
- Endpoint locale validato da `validate_provider_url(..., allow_public=False)` (default `http://127.0.0.1:11434`, nessuna esposizione LAN/WAN).
- Verifica preventiva su `/api/tags` della disponibilità del servizio e del modello configurato.
- Parametri `/api/chat`: `stream: false`, `options.num_predict` (`JARVIS_OLLAMA_MAX_TOKENS`), `options.temperature` (`JARVIS_OLLAMA_TEMPERATURE`).
- Nessuna esecuzione di comandi dal testo generato.

### Provider Cloud (`CloudAIClient`)
- Adapter compatibile con API OpenAI Chat Completions (`/chat/completions`).
- Parametri: `JARVIS_CLOUD_PROVIDER`, `JARVIS_CLOUD_BASE_URL`, `JARVIS_CLOUD_MODEL`, `JARVIS_CLOUD_API_KEY`, `JARVIS_CLOUD_TIMEOUT_S`, `JARVIS_CLOUD_MAX_TOKENS`, `JARVIS_CLOUD_TEMPERATURE` (omessa se `none`), `JARVIS_CLOUD_MAX_REQUESTS_PER_HOUR`, `JARVIS_CLOUD_MAX_DAILY_TOKENS`.
- Gestione dedicata HTTP `401/403`, `404`, `429` (rate limit/quota), `5xx`, timeout e risposte vuote.

## 4. Modalità di routing

| Modalità (`JARVIS_AI_MODE`) | Comportamento | Fallback |
|---|---|---|
| `DISABLED` (default) | Salta Ollama e Cloud; mantiene solo `LocalIntentHandler` + `OfflineFallbackProvider` | Nessuno |
| `LOCAL_ONLY` | Usa solo Ollama locale | Solo `OfflineFallbackProvider` |
| `CLOUD_ONLY` | Usa solo Cloud HTTPS | Solo `OfflineFallbackProvider` |
| `LOCAL_FIRST` | Prova Ollama | Passa a Cloud **solo se** `JARVIS_AI_FALLBACK_ENABLED=true` e Cloud configurato |
| `CLOUD_FIRST` | Prova Cloud | Passa a Ollama **solo se** `JARVIS_AI_FALLBACK_ENABLED=true` e Ollama disponibile |

## 5. Sicurezza e gestione dei segreti

- API key caricata esclusivamente da variabili d'ambiente (`JARVIS_CLOUD_API_KEY` o `OPENAI_API_KEY`), mai hardcoded o salvata nel repository.
- `BridgeDiagnostics` (`redact_secrets`) maschera `device_token`, `esp_device_token`, `cloud_api_key`, token `Bearer` e pattern `sk-...` / `AIza...` dai log.
- Nessun segreto viene inviato all'ESP32-S3 nei payload WSS.
- HTTPS obbligatorio e guardia anti-SSRF su `validate_cloud_url()` per impedire richieste verso IP privati, loopback o `.local`.
- Protezione anti-prompt-injection in `conversation.py` (`sanitize_message_text`) + istruzione di sistema dedicata.
- Nessuna registrazione delle trascrizioni complete nei log ordinari (`JARVIS_LOG_CONVERSATION_TEXT=false`).

## 6. Memoria conversazionale

- Limite in RAM per la sola sessione corrente (`JARVIS_CONVERSATION_MAX_MESSAGES=8`, `JARVIS_CONVERSATION_MAX_TOKENS=1200`).
- Nessuna persistenza su disco o NAS in questa fase.
- Azzeramento contesto tramite endpoint `POST /api/v1/conversation/reset` oppure comandi vocali deterministici (`"nuova conversazione"`, `"azzera il contesto"`, `"azzera la conversazione"`).
- I messaggi di errore `offline_fallback` non vengono salvati nella cronologia LLM.

## 7. Test eseguiti

Suite `test_hybrid_ai_fase12.py` (con `httpx.MockTransport` e motori STT/TTS simulati) + regressione Voice Bridge / ESP32 WSS / Voice Lab:
- Coperti tutti i 16 scenari richiesti (Ollama disponibile/indisponibile/modello mancante, Cloud simulato, API key mancante, timeout senza retry duplicati, rate limit HTTP 429 e limiti locali, risposta vuota, fallback abilitato/disabilitato, contesto multi-turno e prompt injection, reset contesto, comandi locali invariati, assenza segreti nei log, troncamento TTS lungo, concorrenza/cancellazione, regressione WSS).

## 8. Benchmark disponibili (reali su questo PC)

- **Hardware misurato**: AMD Ryzen 7 5700U (8C/16T), **15.39 GB RAM totali**, **4.23 GB RAM liberi** con IDE e Voice Bridge attivi, **326.46 GB** liberi su `C:`.
- **Pipeline vocale reale osservata (`task-3456`, Whisper `small/int8` + Piper `it_IT-riccardo-x_low`)**:
  - STT (`small/int8`, clip ~2.3–3.1s): `~2818–3723 ms`
  - AI (`Local Intent` / `offline_fallback`): `< 1 ms`
  - TTS (Piper): `~595–1726 ms`
  - Totale turno senza LLM: `~3452–5470 ms`
- **Modelli Ollama/Cloud**: nessun benchmark di latenza LLM generato perché Ollama e Cloud non sono ancora stati attivati (coerente con i vincoli di FASE 12).

## 9. Limiti noti

- Con IDE e Whisper `small/int8` attivi restano ~4.23 GB di RAM libera: modelli Ollama > 4 GB (es. 7B) causerebbero swapping su Windows 11 16 GB.
- Ollama (`%USERPROFILE%\AppData\Local\Programs\Ollama\ollama.exe`) è installato con `qwen2.5:3b` già in cache locale (`~/.ollama/models`), ma il demone è attualmente fermo (`127.0.0.1:11434` chiuso).
- Il volume speaker impostato via seriale (`VOL 13`) non è persistente al riavvio (default firmware `10%`).

## 10. Procedura di rollback

1. Impostare `JARVIS_AI_MODE=DISABLED` e `JARVIS_AI_FALLBACK_ENABLED=false` (valori predefiniti).
2. Riavviare il Voice Bridge con gli stessi parametri precedenti: il sistema torna immediatamente al comportamento precedente (`LocalIntentHandler` + `OfflineFallbackProvider`).

## 11. Piano di attivazione controllata (in attesa di autorizzazione)

1. **Test iniziale solo locale (`LOCAL_ONLY`)**:
   - Avviare il servizio Ollama locale vincolato a `127.0.0.1:11434`.
   - Impostare `JARVIS_AI_MODE=LOCAL_ONLY`, `JARVIS_OLLAMA_ENABLED=true`, `JARVIS_OLLAMA_MODEL=qwen2.5:3b`, `JARVIS_AI_FALLBACK_ENABLED=false`.
   - Verificare `/ready` e misurare latenza reale e RAM con 3–5 domande vocali su `GPIO47`.
2. **Test opzionale Cloud (`CLOUD_ONLY` o `LOCAL_FIRST`)**:
   - Impostare `JARVIS_CLOUD_API_KEY` nella sessione (mai in file tracciati), `JARVIS_CLOUD_ENABLED=true`, `JARVIS_CLOUD_PROVIDER=openai`, `JARVIS_CLOUD_MODEL=gpt-4o-mini`, limiti `JARVIS_CLOUD_MAX_REQUESTS_PER_HOUR=30`.
   - Abilitare `JARVIS_AI_FALLBACK_ENABLED=true` solo se si desidera il passaggio automatico al Cloud quando Ollama è spento o in timeout.
