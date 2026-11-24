# FASE 11.3C.6 — Diagnostica riconoscimento vocale e instradamento AI

> **Stato**: Solo analisi e diagnostica. Nessuna modifica applicata al codice, al firmware ESP32, al firewall o ai servizi; nessun modello AI installato.

---

## 1. Origine esatta dei messaggi «motore AI non attivo / non raggiungibile»

I messaggi segnalati provengono da [offline_fallback.py](05-Voice-AI/voice_bridge/offline_fallback.py) (`OfflineFallbackProvider.generate_reply`, righe 14–32), richiamato da [ai_router.py](05-Voice-AI/voice_bridge/ai_router.py) (`AIRouter.route`, Priorità 3):

- **Saluti (`"ciao"`, `"buongiorno"`, `"buonasera"`, `"salve"`)** → riga 18:
  `"Ciao! Al momento il motore AI non è raggiungibile, ma sono operativo in modalità locale."`
- **Ora in fallback (`"che ore sono"` / `"che ora è"`)** → riga 23:
  `"Sono le HH:MM. Il motore AI è attualmente offline."`
- **Stato (`"stato"`, `"come stai"`, `"ci sei"`)** → riga 26:
  `"Sono pronto e il sistema locale funziona, ma il motore AI principale non è al momento disponibile."`
- **Qualsiasi altra frase (catch-all)** → riga 30:
  `"Al momento non riesco a contattare il motore AI. Riprova quando il servizio sarà disponibile."`

## 2. Stato reale dei provider AI sul PC

- **Ollama**: `OLLAMA_RUNNING=False` (nessun processo `ollama` in esecuzione su `127.0.0.1:11434`); inoltre il server Voice Bridge di collaudo (`task-3345`, `PID 11300`) è stato avviato esplicitamente con `JARVIS_OLLAMA_ENABLED="false"` e `JARVIS_CLOUD_ENABLED="false"`.
- **Cloud API**: disabilitata (`JARVIS_CLOUD_ENABLED="false"`).
- **`.env` in `05-Voice-AI/`**: assente (`ENV_FILE_EXISTS=False`).
- **Provider effettivamente attivi durante il test**:
  - Priorità 0: `LocalIntentHandler` (`local_intents.py`) — solo comandi deterministici di ora/giorno/data.
  - Priorità 3: `OfflineFallbackProvider` (`offline_fallback.py`).

## 3. Log disponibili e stato audio ESP32

- Nei log di `uvicorn` (`task-3345`) risultano le connessioni WebSocket ESP32 accettate (`<ESP32_LAN_IP>:52720` e `<ESP32_LAN_IP>:50699`), mentre il logger `jarvis.voice_bridge` (`BridgeDiagnostics`) non emette su stdout di `uvicorn` perché privo di `StreamHandler` configurato; inoltre `log_conversation_text=False` (corretto per la privacy) non salva trascrizioni su disco.
- Pertanto le trascrizioni storiche delle singole domande pronunciate sull'ESP32 non sono recuperabili dai log passati, ma il fatto che alcune domande abbiano prodotto risposte corrette e audio comprensibile conferma il funzionamento della catena I²S RX (`INMP441`) → WSS → Whisper `base` → Piper → I²S TX (`MAX98357A`).

## 4. Matrice di test eseguita sul codice reale (`LocalIntentHandler` + `AIRouter`)

Eseguita in sola modalità offline (`ollama_enabled=False`, `cloud_enabled=False`, `timezone="Europe/Rome"`):

| Frase di ingresso (simulata/trascritta) | Provider selezionato | Risposta prodotta |
|---|---|---|
| `"Ciao Jarvis, che ore sono?"` | `Local Intent` | `"Sono le 18 e 53."` |
| `"Che ore sono?"` | `Local Intent` | `"Sono le 18 e 53."` |
| `"Mi dici che ore sono?"` | `offline_fallback` | `"Sono le 18:53. Il motore AI è attualmente offline."` |
| `"Dimmi che ore sono"` | `offline_fallback` | `"Sono le 18:53. Il motore AI è attualmente offline."` |
| `"Che ore sono adesso?"` | `offline_fallback` | `"Sono le 18:53. Il motore AI è attualmente offline."` |
| `"Ciao, che ore sono?"` | `offline_fallback` | `"Ciao! Al momento il motore AI non è raggiungibile, ma sono operativo in modalità locale."` |
| `"Dimmi l'ora"` | `Local Intent` | `"Sono le 18 e 53."` |
| `"Mi dici l'ora per favore?"` | `offline_fallback` | `"Al momento non riesco a contattare il motore AI. Riprova quando il servizio sarà disponibile."` |
| `"Che giorno è oggi?"` | `Local Intent` | `"Oggi è mercoledì 18 novembre 2026."` |
| `"Che data è oggi?"` | `Local Intent` | `"Oggi è il 18 novembre 2026."` |
| `"Ciao Jarvis!"` | `offline_fallback` | `"Ciao! Al momento il motore AI non è raggiungibile, ma sono operativo in modalità locale."` |
| `"Come stai?"` | `offline_fallback` | `"Sono pronto e il sistema locale funziona, ma il motore AI principale non è al momento disponibile."` |
| `"Raccontami una barzelletta"` | `offline_fallback` | `"Al momento non riesco a contattare il motore AI. Riprova quando il servizio sarà disponibile."` |
| `"Ciao, c'è Armis, ghiore se o no?"` | `offline_fallback` | `"Ciao! Al momento il motore AI non è raggiungibile, ma sono operativo in modalità locale."` |

## 5. Cause confermate vs ipotesi

- **Cause confermate (codice + configurazione)**:
  1. **Nessun motore AI generativo attivo** (`Ollama` non in esecuzione e `Cloud` disabilitata): qualsiasi domanda fuori da `LocalIntentHandler` finisce necessariamente in `OfflineFallbackProvider`.
  2. **Matching troppo rigido in `LocalIntentHandler`** ([local_intents.py](05-Voice-AI/voice_bridge/local_intents.py), righe 159–165): accetta solo un insieme chiuso di stringhe esatte. Parafrasi naturali come `"Mi dici che ore sono?"`, `"Che ore sono adesso?"` o `"Mi dici l'ora per favore?"` falliscono e cadono in `offline_fallback`.
  3. **Ordine errato e prefisso rigido in `OfflineFallbackProvider` / `_PREFIX_RE`**: se Whisper trascrive `"Ciao, che ore sono?"` (senza `"Jarvis"`), `_PREFIX_RE` non rimuove `"ciao"` da solo e `OfflineFallbackProvider` intercetta `"ciao"` prima di `"che ore sono"`, rispondendo che il motore AI non è raggiungibile invece di dare l'ora.
  4. **Assenza di log diagnostici su console (`BridgeDiagnostics`)**: senza un handler di log non sensibile su console per `provider_used`, `input_rms_16`, `input_peak_16`, `stt_ms`, non è immediato distinguere a colpo d'occhio un errore STT da un mancato match di `LocalIntentHandler`.
- **Ipotesi da verificare (solo con log metriche abilitati)**:
  - Eventuali errori parziali di trascrizione di Whisper `base` sull'audio INMP441 (es. `"Jarvis"` omesso o alterato) quando la frase non viene pronunciata in forma canonica.

## 6. Correzioni proposte in ordine di priorità (in attesa di autorizzazione)

1. **[Priorità 1 — Bug] Ampliare in modo pulito e sicuro `LocalIntentHandler`** ([local_intents.py](05-Voice-AI/voice_bridge/local_intents.py)):
   - Gestire saluti iniziali opzionali (`ciao`, `ehi`, `salve`, `buongiorno`, `buonasera`, con o senza `jarvis`) e cortesia finale (`per favore`, `adesso`, `ora`, `oggi`).
   - Supportare parafrasi chiare di ora/giorno/data (`mi dici che ore sono`, `dimmi che ore sono`, `sai che ore sono`, `mi dici l'ora`, `che giorno è`, `che data è`) senza forzare frasi corrotte.
2. **[Priorità 2 — Bug] Sistemare `OfflineFallbackProvider`** ([offline_fallback.py](05-Voice-AI/voice_bridge/offline_fallback.py)):
   - Controllare richieste di ora/data **prima** dei saluti (`"ciao"`), e rendere chiara la risposta ai saluti puri senza sembrare un guasto improvviso.
3. **[Priorità 3 — Diagnostica] Aggiungere log metriche non sensibili su console** in `BridgeDiagnostics` / `esp_protocol.py` (`provider_used`, `input_rms_16`, `input_peak_16`, `input_duration_s`, `stt_ms`, `ai_ms`, `tts_ms` — mai trascrizioni o segreti di default).
4. **[Priorità 4 — Configurazione AI futura, fuori da bug]**:
   - Quando si vorranno risposte conversazionali generiche, configurare **Ollama** (sul PC Windows) o un provider **Cloud** autorizzato in `.env` (perché finché entrambi sono disattivati, qualsiasi domanda generica riceverà sempre il fallback offline).
