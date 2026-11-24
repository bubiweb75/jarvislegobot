# FASE 12.15A — Confronto voce Piper: simulazione vs robot reale

## 1. Configurazione originale verificata ("JARVIS Amichetto")

Fonte verificata nel repository:
- `05-Voice-AI/config.py` (`JarvisConfig`, righe 36–42)
- `05-Voice-AI/tts_providers.py` (`PiperWithFallbackTTSProvider`, righe 168–314)
- `05-Voice-AI/voice_dsp.py` (`shape_piper_wav`, righe 76–122)

### Parametri nativi Piper CLI
- Modello: `it_IT-riccardo-x_low.onnx` (`sample_rate` nativo da JSON: `16000 Hz`, `noise_scale` default modello `0.667`, `length_scale` default `1`).
- `--length_scale`: `0.826` (`1.0 / 1.21`, cioè velocità **`1.21x`**).
- `--noise_scale`: **`1.10`** (`piper_noise_scale=1.10`).

### Elaborazione audio successiva (`voice_dsp.py` / `shape_piper_wav`)
- **Pitch**: **`+5.0` semitoni** tramite phase vocoder + interpolazione lineare (preserva la durata).
- **`robot_mix`**: **`0.0`** (disattivato; l'effetto metallico entra solo per `> 0.005`).
- **Normalizzazione / soft-limiter**: massimizzatore RMS (`gain = min(5.0, 0.48 / active_rms)`) seguito da soft-limiter **`tanh`** (`np.tanh((samples * gain) / 0.96) * 0.96`) e clip finale `[-0.98, 0.98]`.
- **Volume TTS digitale**: **`100%`** (`volume=100` in `JarvisConfig.tts_volume`, distinto dal volume hardware/firmware dell'amplificatore ESP32).

## 2. Configurazione attuale del Voice Bridge

Fonte verificata: `05-Voice-AI/voice_bridge/tts_engine.py` (`PiperTTSEngine`, righe 31–98) e `05-Voice-AI/voice_bridge/audio.py`.

- Esegue `piper.exe --model it_IT-riccardo-x_low.onnx --output_file <tmp.wav>` **senza** `--length_scale` né `--noise_scale` (usa i default del modello: velocità `1.00x`, `noise_scale=0.667`).
- Non applica `shape_piper_wav`: pitch **`0` semitoni**, `robot_mix = 0.0`, nessun massimizzatore RMS / soft-limiter `tanh`.
- Normalizza il formato tramite `validate_and_normalize_wav()` a **`16000 Hz`, mono, PCM16** (nessun effetto su pitch/velocità/timbro).

## 3. Tabella comparativa

| Parametro | Simulazione ("JARVIS Amichetto") | Voice Bridge attuale | Differenza e impatto |
|---|---|---|---|
| Modello Piper | `it_IT-riccardo-x_low.onnx` (`config.py`, `tts_providers.py`) | `it_IT-riccardo-x_low.onnx` (`tts_engine.py`) | Nessuna differenza di modello |
| Velocità (`--length_scale`) | `1.21x` (`--length_scale 0.826`) | Default modello (`1.00x`, nessun flag) | Voce attuale più lenta (`+2.0s` sul testo di prova) |
| `noise_scale` | `1.10` (`--noise_scale 1.10`) | Default modello (`0.667`, nessun flag) | Simulazione leggermente più espressiva/variabile |
| Pitch (post-DSP) | `+5.0` semitoni (phase vocoder `voice_dsp.py`) | `0` semitoni (nessun DSP) | Voce attuale più grave/adulta; simulazione più acuta/giovanile |
| `robot_mix` (post-DSP) | `0.0` (`voice_dsp.py`) | `0.0` (assente) | Nessuna differenza |
| Normalizzazione / Limiter | RMS maximizer + `tanh` soft-limiter (`voice_dsp.py`) | Nessuno (`validate_and_normalize_wav` solo formato) | Simulazione molto più presente (`rms=11382` vs `6332`, `0` clipped vs `3`) |
| Volume digitale TTS | `100%` (`JarvisConfig.tts_volume`) | `100%` implicito (non attenuato) | Nessuna attenuazione digitale lato bridge |
| Formato PCM per ESP32 | `16000 Hz`, mono, `16-bit` PCM | `16000 Hz`, mono, `16-bit` PCM | Identico |

## 4. Misurazione isolata su testo italiano identico (436 caratteri)

Test eseguito con `compare_piper_voices.py` sullo stesso testo esplicativo da `436` caratteri (nessun audio inviato al robot):

| Configurazione | Tempo sintesi | Sample rate / Formato | Durata | Dimensione PCM | RMS / Picco | Clipping |
|---|---|---|---|---|---|---|
| **Voice Bridge attuale** | `1682.0 ms` | `16000 Hz`, mono, 16-bit | `25.10 s` | `803,072 B` | `6332` / `32767` | `3` campioni |
| **Simulazione (output `shape_piper_wav`)** | `1909.8 ms` (`1652.7` Piper + `257.0` DSP) | `16000 Hz`, mono, 16-bit | `23.10 s` | `739,132 B` | `11382` / `31454` | `0` campioni |
| **Simulazione + `validate_and_normalize_wav`** | `2029.8 ms` | `16000 Hz`, mono, 16-bit | `23.10 s` | `739,132 B` | `11382` / `31454` | `0` campioni |

Osservazione chiave: la velocità nominale `1.21x` ha ridotto la durata reale da `25.10s` a `23.10s` (**`-7.97%`**, non `-17.4%`, perché le pause e il resintetizzatore non scalano linearmente).

## 5. Valutazione tecnica

1. **Corrispondenza**: no, il Voice Bridge attuale usa la voce base di Riccardo (`1.00x`, `0` semitoni, senza `tanh`), diversa da "JARVIS Amichetto".
2. **Riproducibilità sul robot**: sì, è pienamente riproducibile sul PC prima dell'invio WSS perché il modello è già nativamente `16000 Hz` mono e `voice_dsp.py` richiede solo `numpy` (già installato in `.venv`).
3. **Modifiche necessarie**: estendere `PiperTTSEngine` (`tts_engine.py`) e `BridgeConfig` per passare `--length_scale` (`0.826`) e `--noise_scale` (`1.10`) a Piper CLI e applicare opzionalmente `shape_piper_wav(pitch_semitones=5.0, robot_mix=0.0, volume=100)`.
4. **Impatto su `TTS_TOO_LONG` (`640,000` B / `20.0s`)**: aiuta marginalmente (`-2.0s` / `-64 KB` su 436 char), **ma non risolve da solo** `TTS_TOO_LONG` (`739,132 B` > `640,000 B`). Restano necessari `JARVIS_TTS_MAX_CHARS` allineato a `~300–340` caratteri (o controllo diretto su `esp_max_tts_bytes`) e risposte più concise.
5. **Rischi per qualità, latenza e memoria**:
   - **Latenza**: `+~257 ms` di CPU DSP per turno (`phase vocoder`).
   - **Volume percepito sullo speaker ESP32**: `rms` quasi raddoppia (`6332 → 11382`, ~`+5.1 dB`); con il firmware a `10%` (o `13%` via seriale) il volume percepito aumenterà sensibilmente senza introdurre clipping digitale (`clipped=0`), ma andrà riverificato acusticamente.
   - **Memoria**: trascurabile (array float32 temporanei di poche centinaia di KB).

## 6. Raccomandazione

Per riallineare il robot alla voce "JARVIS Amichetto" e risolvere contemporaneamente `TTS_TOO_LONG` nella FASE 12.15B:
1. Integrare in `PiperTTSEngine` i parametri configurabili di "JARVIS Amichetto" (`speed=1.21`, `noise_scale=1.10`, `pitch=5.0`, `tanh` limiter).
2. Allineare `JARVIS_TTS_MAX_CHARS=340` (coerente con `1.21x` e `< 20.0s` / `< 640,000 B`), aggiungere il log `WARNING` su `TTS_TOO_LONG` in `esp_protocol.py` e ridurre `JARVIS_OLLAMA_MAX_TOKENS=95` per risposte più rapide e complete sotto i 20 secondi.
