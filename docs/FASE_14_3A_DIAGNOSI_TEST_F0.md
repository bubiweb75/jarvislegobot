# FASE 14.3A — Diagnosi Test F0 Profilo 08 e Sblocco Pubblicazione GitHub

Data: `2026-11-24` | Ambito: `05-Voice-AI/tests/test_fase12_24_wsola_profile08.py` (nessuna modifica alla pipeline audio di produzione).

---

## 1. Causa Identificata

Il fallimento di `test_real_piper_profile08_if_available` (`AssertionError: 158.4158... not greater than 165.0`) era causato **esclusivamente dal metodo di stima `_estimate_f0_hz` del test**, non dalla pipeline `Piper + WSOLA`:
- `_estimate_f0_hz` estraeva **una sola finestra di `40 ms`** esattamente al `25%` della durata totale (`s[len(s)//4 : ...]`), senza filtrare pause, consonanti sorde o picchi di autocorrelazione deboli.
- Con `noise_scale = 0.60`, la naturale variabilità prosodica di Piper poteva far cadere quel singolo istante al `25%` su una transizione non vocalizzata o subarmonica, producendo una stima spuria (`158.4 Hz`).

---

## 2. Risultati Sperimentali (10 Ripetizioni × 3 Frasi = 60 Sintesi)

Misurazione su `it_IT-riccardo-x_low.onnx` (`speed=1.00`, `noise_scale=0.60`), confrontando sintesi originale (`dsp_enabled=False`) vs Profilo 08 (`WSOLA`, `+5.0` semitoni, rapporto teorico `2^(5/12) ≈ 1.3348`) mediante **mediana multi-frame sui soli frame sonori** (`win=40 ms`, `hop=15 ms`, `rms >= 0.02`, `ac_peak >= 0.45`):

| Frase | `raw` mediana [min..max] | Profilo 08 mediana [min..max] | Rapporto medio [min..max] |
|---|---|---|---|
| **S1**: *"Dodici per otto fa novantasei."* | `152.5 Hz` `[148.1..158.4]` | **`199.7 Hz`** `[192.8..205.1]` | **`1.3097`** `[1.2590..1.3590]` |
| **S2**: *"Ciao! Come stai oggi? Tutto bene, grazie."* | `157.4 Hz` `[149.5..170.2]` | **`207.3 Hz`** `[195.1..217.7]` | **`1.3187`** `[1.2208..1.4459]` |
| **S3**: *"Il vulcano erutta magma, gas e cenere dalla camera magmatica."* | `156.0 Hz` `[149.5..163.3]` | **`208.1 Hz`** `[200.0..213.3]` | **`1.3345`** `[1.2895..1.4000]` |

**Conclusione sperimentale**: in **30/30** sintesi Profilo 08 la mediana sonora è sempre compresa tra `192.8 Hz` e `217.7 Hz` (contro `148.1–170.2 Hz` del baseline non shiftato), con rapporto medio `1.31–1.335` coerente con `+5` semitoni.

---

## 3. Modifica Effettuata al Test e Motivazione Tecnica

In [test_fase12_24_wsola_profile08.py](../05-Voice-AI/tests/test_fase12_24_wsola_profile08.py):
1. **`_estimate_f0_hz(wav_bytes)`**: sostituita la singola finestra al `25%` con la **mediana su tutti i frame sonori** (`40 ms`, `hop 15 ms`, `rms >= 0.02`, autocorrelazione normalizzata `>= 0.45`).
2. **`test_real_piper_profile08_if_available`**:
   - Verifica `120.0 < f0_raw < 180.0` sul baseline non elaborato (`dsp_enabled=False`).
   - Applica `shape_piper_wav(..., pitch_semitones=5.0, method="wsola", limiter_enabled=False)` sulla **medesima** sintesi `raw_wav` (eliminando la varianza stocastica tra due chiamate Piper) e verifica rapporto `1.28 <= f0_same / f0_raw <= 1.39` e conservazione durata `abs(dur_same_s - dur_raw) <= 0.05 s`.
   - Verifica `f0 >= 180.0 Hz`, formato `16 kHz mono 16-bit` e limite `<= 640.000 B` su `PiperTTSEngine` Profilo 08 completo.

### Verifica capacità di rilevare regressioni
- Se `WSOLA` non applica lo shift (`pitch=0.0` / `dsp_enabled=False`), `ratio ≈ 1.00` fallisce `>= 1.28` e `f0_raw < 180.0 Hz` fallisce `>= 180.0 Hz`.
- Se il pitch shift altera la durata (es. resampling semplice invece di WSOLA), `abs(dur_same_s - dur_raw) <= 0.05 s` fallisce.

---

## 4. Risultati Finali delle Suite

| Suite | Esito | Note |
|---|---|---|
| **Test specifico Profilo 08** (`test_fase12_24_wsola_profile08.py`) | **`7/7` OK** (`5.26 s`) | Nessun skip, nessun relax |
| **Voice Bridge (`05-Voice-AI/tests`)** | **`104/104` OK** (`26.04 s`) | `task-4907` |
| **Unit test firmware (`test_fase13_4_logic.py`)** | **`6/6` OK** (`0.003 s`) | `task-4895` |
| **Backend Robotics Platform (`JARVIS-Robotics-Platform/tests`)** | **`15/15` OK** (`0.030 s`) | `task-4895` |
| **Frontend Robotics Platform (`vitest` + `tsc && vite build`)** | **`19/19` OK + build OK** (`4.58 s`) | `task-4895` |

---

## 5. Conferma Integrità Produzione
- `voice_dsp.py`, `voice_bridge/`, `Piper Profilo 08` (`speed=1.00`, `noise_scale=0.60`, `pitch=+5.0`, `wsola`, `no tanh`), firmware ESP32-S3 (`FASE 13.8`), `Eyes 3.0`, `microWakeWord`, `VAD` e configurazioni operative sono rimasti **totalmente invariati**.

In attesa di autorizzazione esplicita per riprendere la **FASE 14.3** (`git add`, `commit`, `tag v1.3.8-stable` e `push`).
