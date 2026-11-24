# FASE 11.3C.10 — Diagnostica temporanea STT e ripristino Voice Bridge

> **Stato**: Raccolta trascrizioni completata, diagnostica disattivata (`JARVIS_LOG_STT_DIAG_TEXT=false`), log temporaneo `task-3423.log` eliminato e Voice Bridge ripristinato (`PID 8100` su `https://<PC_LAN_IP>:8765` con ESP32-S3 riconnesso). Nessuna correzione ancora applicata al riconoscimento vocale.

---

## 1. Risultati reali raccolti dalle tre prove vocali (`PID 12284`)

| # | Frase pronunciata | Request ID | Trascrizione Whisper (`base/int8`) | Provider | Durata | RMS | Picco | Tempo STT |
|---|---|---|---|---|---|---|---|---|
| 1 | `"Ciao Jarvis, che ore sono?"` | `req_717871c88309` | `"Ciao Jarvis che ora sono"` | `offline_fallback` | `2.94 s` | `4928` | `32767` | `1971.0 ms` |
| 2 | `"Mi dici che ore sono?"` | `req_40f97029e729` | `"Medici che è rsono"` | `offline_fallback` | `2.85 s` | `2354` | `18369` | `827.2 ms` |
| 3 | `"Che giorno è oggi?"` | `req_e82f2d68cfc6` | `"che giorno è oggi"` | `Local Intent` | `2.40 s` | `3469` | `27086` | `800.6 ms` |

## 2. Analisi della causa

1. **Frase 1 (`"Ciao Jarvis, che ore sono?"` → `"Ciao Jarvis che ora sono"`)**:
   - **Causa confermata (doppia)**: Whisper `base/int8` ha confuso `"ore"` con `"ora"` (`"che ora sono"` anziché `"che ore sono"`), e `LocalIntentHandler` / `OfflineFallbackProvider` prevedevano `"che ore sono"` o `"che ora è"`, ma **non** `"che ora sono"`.
   - Sul segnale audio si nota `peak=32767` (raggiungimento del fondo scala su almeno un picco, che da solo non dimostra clipping prolungato ma può contribuire a una lieve distorsione di vocale finale).
2. **Frase 2 (`"Mi dici che ore sono?"` → `"Medici che è rsono"`)**:
   - **Causa confermata**: errore di riconoscimento acustico-lessicale di **Whisper `base/int8`** sull'italiano (`"Mi dici"` → `"Medici"`, `"che ore sono"` → `"che è rsono"`), con `RMS 2354` e `picco 18369` (nessuna saturazione). Una trascrizione così alterata non deve essere forzata in `LocalIntentHandler`.
3. **Frase 3 (`"Che giorno è oggi?"` → `"che giorno è oggi"`)**:
   - Riconosciuta alla perfezione da Whisper `base/int8` e gestita correttamente da `Local Intent`.

## 3. Correzione minima consigliata (in attesa di autorizzazione)

1. **Test comparativo con Whisper `small` (`int8`) già in cache locale** (scaricato nella FASE 11.2C.5) sul Voice Bridge, per verificare se migliora il riconoscimento italiano di `"Mi dici che ore sono?"` e `"che ore sono"` mantenendo tempi accettabili (< ~1,5–2 s).
2. **Eventuale aggiunta in `LocalIntentHandler`** della sola variante fonetica grammaticalmente vicina `"che ora sono"` (poiché in italiano parlato/STT `"ora"`/`"ore"` è una minima confusione di singolare/plurale sul comando esplicito di ora), **senza** mai forzare trascrizioni corrotte come `"Medici che è rsono"`.

## 4. Esito ripristino Voice Bridge e pulizia log

- **Processo diagnostico `PID 12284`**: arrestato ordinatamente (`Stop-Process -Id 12284`).
- **Log temporaneo `task-3423.log`**: eliminato (`DELETED_DIAG_LOG=True`, `DIAG_LOG_EXISTS_AFTER=False`); nessuna trascrizione salvata in `.env`, DB o log permanenti.
- **Diagnostica disabilitata**: `BridgeConfig.from_env().log_stt_diag_text == False`.
- **Nuovo Voice Bridge attivo (`PID 8100`, `task-3437`)**: in ascolto su `https://<PC_LAN_IP>:8765` con WSS/TLS, `base`, `Europe/Rome`, Ollama/Cloud disabilitati.
- **Verifiche post-riavvio**: `RESTORED_WSS_AUTH_PING_OK=True` e riconnessione automatica dell'ESP32-S3 (`<ESP32_LAN_IP>:50708`) confermata nei log.
