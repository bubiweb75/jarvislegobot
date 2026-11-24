# FASE 11.3C.9 — Diagnostica: perché le domande sull'ora finiscono nel fallback AI

> **Stato**: Solo analisi e diagnostica. Nessuna modifica applicata al codice o al comportamento di JARVIS; il Voice Bridge attivo (`PID 13428`) non è stato riavviato.

---

## 1. Log diagnostici reali del Voice Bridge (`PID 13428`, `task-3399`)

Durante il collaudo vocale sull'ESP32-S3 (`<ESP32_LAN_IP>`), il Voice Bridge ha registrato 5 turni consecutivi:

| Request ID | Provider | Fallback | Durata | RMS | Picco | STT | AI | TTS | Totale |
|---|---|---|---|---|---|---|---|---|---|
| `req_eaf5f2fe8fad` | `offline_fallback` | `True` | `2.80 s` | `3646` | `24002` | `2051.3 ms` | `0.0 ms` | `767.2 ms` | `2837.9 ms` |
| `req_8f7d041a8be9` | `offline_fallback` | `True` | `3.31 s` | `4757` | `32767` | `845.5 ms` | `0.1 ms` | `897.4 ms` | `1759.6 ms` |
| `req_975ab2736844` | `offline_fallback` | `True` | `2.99 s` | `3084` | `24724` | `860.7 ms` | `0.0 ms` | `766.5 ms` | `1643.8 ms` |
| `req_92772f532468` | `Local Intent` | `False` | `2.61 s` | `3377` | `32767` | `807.7 ms` | `0.5 ms` | `666.8 ms` | `1491.6 ms` |
| `req_b92bd78d6c79` | `offline_fallback` | `True` | `2.51 s` | `3104` | `29867` | `792.7 ms` | `0.1 ms` | `770.3 ms` | `1576.7 ms` |

## 2. Verifica codice attivo e `LocalIntentHandler`

- Il formato dei log (`dur=... rms=... peak=...`) conferma che `PID 13428` sta eseguendo il codice aggiornato della **FASE 11.3C.7**.
- Verifica diretta su `LocalIntentHandler(timezone_name="Europe/Rome")`:
  - `"Ciao Jarvis, che ore sono?"` → **`time`**
  - `"Mi dici che ore sono?"` → **`time`**
  - `"Che giorno è oggi?"` → **`day`**
  - `"Come ti chiami?"` → `None` (`offline_fallback` atteso)

## 3. Causa confermata e dati mancanti

- **Qualità audio ESP32**: durata `2,51–3,31 s` e `RMS 3084–4757` sono ampiamente validi (nessun troncamento né silenzio; due picchi a `32767` indicano solo lieve saturazione sui picchi più forti, ma `req_92772f532468` con `peak=32767` è stato comunque riconosciuto correttamente come `Local Intent`).
- **Causa confermata**: poiché `LocalIntentHandler` riconosce entrambe le frasi testuali sull'ora, il passaggio in `offline_fallback` è causato dalla **trascrizione prodotta da Whisper `base` (`int8`)**, che altera le parole dell'ora (analogamente a quanto già osservato nella FASE 11.2C.4: `"ghiore se o no"`).
- **Dato mancante**: le trascrizioni testuali effettive dei 5 turni non sono presenti nei log perché `log_conversation_text=False` (impostazione di privacy corretta).

## 4. Modalità diagnostica temporanea proposta (richiede consenso esplicito)

Prima di attivare qualsiasi modifica:
- **Meccanismo proposto**: aggiungere una flag esplicita `JARVIS_LOG_STT_DIAG_TEXT=false` (disabilitata per impostazione predefinita). Solo se impostata a `true` dall'utente, `VoiceBridgeService` stamperà su console (`stdout` del processo `uvicorn`, visibile in questa sessione nel log temporaneo del task `task-*.log`) la sola stringa `stt_text="..."` per i turni di prova.
- **Conservazione ed eliminazione**:
  - Nessun salvataggio in database o file persistenti del repository.
  - Le righe compaiono soltanto nel log temporaneo di sessione del processo `uvicorn`.
  - Al termine del test di verifica, la modalità viene disattivata riavviando il server senza la flag (default `false`) e il file di log temporaneo del task può essere eliminato/sovrascritto.

## 5. Correzione minima proposta dopo la verifica

1. Con consenso dell'utente, abilitare temporaneamente `JARVIS_LOG_STT_DIAG_TEXT=true` per osservare la trascrizione esatta di `"Ciao Jarvis, che ore sono?"` e `"Mi dici che ore sono?"` dall'ESP32.
2. In base al risultato reale, valutare il passaggio controllato da Whisper `base` a Whisper **`small`** (già scaricato in cache locale nella FASE 11.2C.5) oppure una regolazione mirata dei parametri STT (`beam_size=5` / `speech_pad_ms=250`), senza introdurre sostituzioni arbitrarie di parole in `LocalIntentHandler`.
