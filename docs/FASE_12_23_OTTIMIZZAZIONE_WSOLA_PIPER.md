# FASE 12.23 — Ottimizzazione WSOLA e miglioramento intelligibilità Piper

**Data**: 2026-11-18  
**Stato**: Diagnostica e benchmark isolati completati (nessuna modifica applicata a Voice Bridge live, configurazione Piper, firmware ESP32, Ollama o altri servizi)  
**Testo diagnostico comune**:  
> *"Tre piccoli robot preparano trenta programmi. Il computer controlla correttamente tutti i componenti. Dodici per otto fa novantasei. Leonardo da Vinci progettò macchine straordinarie."*

---

## 1. Analisi del profilo F (WSOLA) e verifica del pitch effettivo

### Funzionamento algoritmico
Il profilo **F** (introdotto nella FASE 12.22) esegue la trasposizione di `+5.0` semitoni in due passi:
1. **Time-stretching nel dominio del tempo (WSOLA)**: allunga il segnale di un fattore `factor = 2^(5/12) ≈ 1.33484` usando `rate = 1 / factor ≈ 0.74915` con finestra Hann da `24 ms` (`384` campioni @ 16 kHz), hop di sintesi `6 ms` (`96` campioni) e raggio di ricerca di cross-correlazione normalizzata `±8 ms` (`±128` campioni, passo `2`).
2. **Ricampionamento lineare (`np.interp`)**: comprime la durata da `round(N * factor)` a `N` campioni originali, traslando tutte le frequenze (F0 e formanti) verso l'alto di `factor` mentre riporta la durata al valore esatto di partenza.

### Verifiche sperimentali
- **Conservazione della durata**: esatta al singolo campione (`11.232 s` / `359.424` byte PCM in ingresso -> `11.232 s` / `359.424` byte PCM in uscita per `05`/`06`).
- **Pitch effettivo misurato (F0 mediana su frame sonori, autocorrelazione normalizzata `70–450 Hz`)**:
  - `01_piper_raw_ns1.10.wav` (`pitch=0`): **`149.53 Hz`** (`430` frame sonori).
  - `05_wsola_orig_ns1.10_pitch5.wav` (`+5 st`): **`197.53 Hz`** (`530` frame sonori) -> rapporto **`1.3210x` (`+4.82` semitoni)** rispetto al target teorico `1.3348x` (`+5.00` st, `199.60 Hz`), scarto `< 0.2` semitoni.
  - `07_wsola_opt_ns0.75_pitch5.wav`: **`195.12 Hz`** (da `148.15 Hz`, `+4.77` st).
  - `08_wsola_opt_ns0.60_pitch5.wav`: **`196.33 Hz`** (da `149.53 Hz`, `+4.72` st).
- **Integrità delle consonanti e compatibilità**: nessuna spalmatura spettrale su finestre da `64 ms` (a differenza del phase vocoder), *crest factor* preservato (`13.09 dB` vs `12.88 dB` del baseline), zero clipping (`0` campioni), formato nativo **PCM16 mono 16.000 Hz**.
- **Uso memoria**: picco Python tracciato con `tracemalloc` pari a **`8.84–9.13 MB`** sul testo diagnostico e **`12.61 MB`** su una risposta lunga da 269 caratteri.

---

## 2. Ottimizzazione delle prestazioni WSOLA (prima / dopo)

Nell'implementazione FASE 12.22 (`wsola_time_stretch_orig`), il ciclo interno Python eseguiva per ogni frame (~1.850 frame) fino a ~129 iterazioni scalari con `np.dot` e `np.sqrt(np.sum(...))`.

### Ottimizzazioni implementate in `wsola_time_stretch_opt` (solo NumPy)
- Precalcolo della finestra `hann` in `float32` e array contiguo `np.ascontiguousarray`.
- Precalcolo dell'energia cumulativa `sq_cumsum` (`float64`) per ottenere la norma di ogni finestra candidata in **O(1)**.
- Vista 2D zero-copy `np.lib.stride_tricks.sliding_window_view(samples, overlap)` e prodotto matrice-vettore BLAS `cands @ ref` in un'unica operazione per frame, eliminando completamente il ciclo interno Python e le allocazioni intermedie.

### Confronto equivalente e tempi reali (senza overhead `tracemalloc`)
- **Equivalenza matematica (`05_wsola_orig` vs `06_wsola_opt`)**: `len = 179.712` campioni identici, **`max_abs_diff = 0.0`**, **`pearson_corr = 1.0`** (risultato **bit-identico**).
- **Latenza DSP reale sul testo diagnostico (`11.232 s` di audio)**:
  - Phase vocoder attuale (`voice_dsp.py`): **`98.6 ms`**
  - WSOLA originale (`FASE 12.22`): **`1444.2 ms`**
  - WSOLA ottimizzato (`step=2`, bit-identico): **`108.2 ms`** (**speedup 13.3x**, solo `+9.6 ms` rispetto al phase vocoder attuale)
  - WSOLA ottimizzato (`step=1`, massima risoluzione): **`173.8 ms`**

*(Nota: nella tabella completa della Sezione 5 sono riportati anche i tempi misurati sotto profiling `tracemalloc`, che introduce overhead su Python pure-loop ma permette di misurare il picco di memoria.)*

---

## 3. Diagnostica Piper (`it_IT-riccardo-x_low.onnx`)

Analisi della sintesi originale di [tts_engine.py](05-Voice-AI/voice_bridge/tts_engine.py) e di [it_IT-riccardo-x_low.onnx.json](05-Voice-AI/tts-lab/models/piper/it_IT-riccardo-x_low.onnx.json):

1. **`noise_scale` elevato rispetto al profilo calibrato del modello**: il JSON ufficiale del modello imposta `"noise_scale": 0.667` (e `"noise_w": 0.8`), mentre il Voice Bridge live usa **`noise_scale = 1.10`** (`1.65x` il valore nominale). Un `noise_scale` alto aumenta la variabilità stocastica del generatore VITS e può impastare le chiusure consonantiche su voci compatte.
2. **Segmentazione del testo e pause**: `PiperTTSEngine.synthesize()` normalizza gli spazi (`" ".join(text.split()).strip()`) e invia il blocco intero a `piper.exe` senza specificare `--sentence_silence` (quindi Piper usa il default interno `0.2 s` tra le frasi) e senza `--noise_w` (default `0.8`).
3. **Limiti intrinseci del modello `x_low`**: `it_IT-riccardo-x_low.onnx` (`26.83 MB`) opera nativamente a `16000 Hz` con qualità `x_low` (nella FASE 12.22 la banda 4–8 kHz rappresentava solo lo `0.38%` dell'energia totale) e presenta `4` campioni a fondo scala (`1.0`) già nel WAV grezzo di Piper.

---

## 4. Confronto `noise_scale` e campioni WSOLA

Tutti i campioni sono stati generati in `05-Voice-AI/tts-lab/samples_fase12_23/` sullo stesso testo diagnostico (`speed=1.00x`). I campioni WSOLA (`05`–`08`) utilizzano normalizzazione lineare sicura (`target_active_rms=0.22`, tetto picco `0.89` = `-1.01 dBFS`, **nessun `tanh`**) per mantenere il livello d'ascolto comparabile ai campioni Piper grezzi (`-12.0` / `-12.9 dBFS`).

| File | Configurazione | Durata (s) | PCM (byte) | Peak (dBFS) | Active RMS (dBFS) | Crest (dB) | Clipping | Silenzio ini/fin (ms) | Max jump / `>0.30` | F0 med. (Hz) | Piper (ms) | DSP real / prof (ms) | Mem (MB) |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `01_piper_raw_ns1.10.wav` | Piper puro `ns=1.10` | 11.232 | 359.424 | -0.00 | -12.88 | 12.88 | 4 | 62.5 / 383.8 | 0.900 / 352 | 149.53 | 1008.3 | 0.0 | 0.0 |
| `02_piper_raw_ns0.90.wav` | Piper puro `ns=0.90` | 11.312 | 361.984 | -0.00 | -12.69 | 12.69 | 4 | 64.4 / 433.1 | 0.723 / 347 | 152.38 | 1003.5 | 0.0 | 0.0 |
| `03_piper_raw_ns0.75.wav` | Piper puro `ns=0.75` | 11.440 | 366.080 | -0.00 | -12.02 | 12.02 | 4 | 58.0 / 398.9 | 0.867 / 565 | 148.15 | 1026.2 | 0.0 | 0.0 |
| `04_piper_raw_ns0.60.wav` | Piper puro `ns=0.60` | 11.632 | 372.224 | -0.00 | -12.22 | 12.22 | 4 | 47.2 / 365.1 | 0.644 / 313 | 149.53 | 1014.2 | 0.0 | 0.0 |
| `05_wsola_orig_ns1.10_pitch5.wav` | WSOLA orig `ns=1.10` `+5` | 11.232 | 359.424 | -1.01 | -14.10 | 13.09 | 0 | 53.0 / 381.0 | 0.745 / 229 | 197.53 | 1008.3 | 1444.2 / 7991.0 | 8.84 |
| `06_wsola_opt_ns1.10_pitch5.wav` | WSOLA opt `ns=1.10` `+5` | 11.232 | 359.424 | -1.01 | -14.10 | 13.09 | 0 | 53.0 / 381.0 | 0.745 / 229 | 197.53 | 1008.3 | **108.2** / 581.2 | 8.84 |
| `07_wsola_opt_ns0.75_pitch5.wav` | WSOLA opt `ns=0.75` `+5` | 11.440 | 366.080 | -1.01 | -13.16 | 12.15 | 0 | 55.3 / 400.2 | 0.599 / 243 | 195.12 | 1026.2 | ~110 / 602.2 | 9.01 |
| `08_wsola_opt_ns0.60_pitch5.wav` | WSOLA opt `ns=0.60` `+5` | 11.632 | 372.224 | -1.01 | -13.38 | 12.36 | 0 | 39.2 / 371.6 | 0.584 / **150** | 196.33 | 1014.2 | ~115 / 636.7 | 9.13 |

### Verifica limite PCM `640.000` byte su risposta lunga (269 caratteri, `MAX_CHARS=270`)
- Test su testo da `269` caratteri con `WSOLA ottimizzato` (`noise_scale=0.75`, `pitch=+5`):
  - Durata: **`15.784 s`**
  - Dimensione PCM: **`505.088` byte** (`<= 640.000` byte, margine di **`134.912` byte**)
  - Sintesi Piper: `1823.0 ms`, picco memoria `12.61 MB`.

---

## 5. Percorsi dei file WAV generati

Cartella: `05-Voice-AI/tts-lab/samples_fase12_23/`

1. `05-Voice-AI/tts-lab/samples_fase12_23/01_piper_raw_ns1.10.wav`
2. `05-Voice-AI/tts-lab/samples_fase12_23/02_piper_raw_ns0.90.wav`
3. `05-Voice-AI/tts-lab/samples_fase12_23/03_piper_raw_ns0.75.wav`
4. `05-Voice-AI/tts-lab/samples_fase12_23/04_piper_raw_ns0.60.wav`
5. `05-Voice-AI/tts-lab/samples_fase12_23/05_wsola_orig_ns1.10_pitch5.wav`
6. `05-Voice-AI/tts-lab/samples_fase12_23/06_wsola_opt_ns1.10_pitch5.wav`
7. `05-Voice-AI/tts-lab/samples_fase12_23/07_wsola_opt_ns0.75_pitch5.wav`
8. `05-Voice-AI/tts-lab/samples_fase12_23/08_wsola_opt_ns0.60_pitch5.wav`

---

## 6. Ricognizione modelli vocali italiani locali

Ricognizione in sola lettura nella directory `05-Voice-AI/tts-lab/models/`:
- `05-Voice-AI/tts-lab/models/piper/it_IT-riccardo-x_low.onnx` (`26.83 MB`, `16000 Hz`, qualità `x_low`, voce maschile — attualmente attivo).
- `05-Voice-AI/tts-lab/models/piper/it_IT-paola-medium.onnx` (`60.57 MB`, `22050 Hz`, qualità `medium`, voce femminile — già presente in locale ma **non** attivo né sostituito).
- *(È presente anche `05-Voice-AI/tts-lab/models/kokoro/kokoro-v1.0.onnx`, motore distinto da Piper).*

Nessun modello è stato scaricato né attivato.

---

## 7. Limiti e raccomandazione tecnica motivata

- **Limiti**: le sole metriche numeriche non misurano la naturalezza fonetica percepita. Inoltre, se il modello `riccardo-x_low` mantiene una lieve sfocatura delle consonanti anche a `noise_scale=0.60` (`04`), ciò riflette il limite di risoluzione acustica `x_low` a `16 kHz`.
- **Raccomandazione tecnica (da confermare solo dopo ascolto)**:
  1. **Sostituire (nella futura fase di attivazione) il phase vocoder + `tanh` con `WSOLA ottimizzato` + normalizzazione lineare sicura**: è **bit-identico** al profilo F già scelto (`pearson_corr = 1.0`), preserva consonanti e dinamica, elimina il clipping e impiega **`108.2 ms`** invece di `1444.2 ms` (`~10 ms` di scarto rispetto al phase vocoder attuale).
  2. **Allineare `noise_scale` vicino al valore calibrato del modello (`0.75` o `0.60` invece di `1.10`)** qualora all'ascolto `07` o `08` risultino più nitidi di `06`.
  3. **In attesa dell'ascolto dell'utente**: nessuna modifica è stata applicata al sistema live.
