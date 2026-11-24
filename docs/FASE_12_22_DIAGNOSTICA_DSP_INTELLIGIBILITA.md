# FASE 12.22 — Diagnostica intelligibilità e isolamento del DSP

**Data**: 2026-11-18  
**Stato**: Diagnostica completata (sola lettura sulla configurazione live; nessuna modifica applicata a Voice Bridge, Piper, ESP32, Ollama o servizi)  
**Testo diagnostico comune**:  
> *"Tre piccoli robot preparano trenta programmi. Il computer controlla correttamente tutti i componenti. Dodici per otto fa novantasei. Leonardo da Vinci progettò macchine straordinarie."*

---

## 1. Analisi dettagliata della catena audio

Percorso end-to-end verificato nel codice sorgente:

1. **Sintesi Piper (`05-Voice-AI/voice_bridge/tts_engine.py`)**:
   - `PiperTTSEngine.synthesize()` invoca `piper.exe` con `--model it_IT-riccardo-x_low.onnx`, `--length_scale {1/speed:.3f}` (a `1.00x` -> `1.000`), `--noise_scale 1.100`.
   - Output nativo del modello `it_IT-riccardo-x_low`: **16.000 Hz, mono, PCM16** (`0.38%` di energia nella banda 4–8 kHz nel campione baseline).
2. **DSP (`05-Voice-AI/voice_dsp.py` -> `shape_piper_wav`)**:
   - **Pitch shifting (`abs(pitch_semitones) >= 0.05`)**: per `+5.0` semitoni calcola `factor = 2**(5/12) ≈ 1.3348`, allunga nel tempo tramite `_phase_vocoder_time_stretch(samples, rate=1/factor)` con **finestra Hann `n_fft=1024` (`64 ms` @ 16 kHz)** e `hop=256` (`16 ms`), poi ricampiona con `np.interp` alla lunghezza originale (`round(len(stretched) / factor)`).
   - **Robot mix**: disattivo (`robot_mix = 0.0`).
   - **Loudness maximizer + soft limiter `tanh` (righe 110–117)**: calcola `active_rms` sui campioni con `|x| > 0.01`, applica `gain = min(5.0, 0.48 / active_rms)` e comprime con `np.tanh((samples * gain) / 0.96) * 0.96`. Nel baseline Piper (`active_rms ≈ 0.232`, `-12.70 dBFS`), `gain ≈ 2.07x`, spingendo i picchi fino a ~`2.07` dentro la saturazione `tanh`.
   - **Output DSP**: `_write_wav_mono_f32` effettua `np.clip(samples, -0.98, 0.98)` e quantizza a `int16` (`* 32767.0`).
3. **Validazione e invio WebSocket (`05-Voice-AI/voice_bridge/audio.py`, `esp_protocol.py`)**:
   - `validate_and_normalize_wav(..., target_sr=16000)` verifica WAV PCM16 mono 16 kHz (nessun ricampionamento necessario perché Piper e DSP operano già a 16 kHz).
   - `esp_protocol.py` verifica `len(out_pcm) <= 640000` byte (20 s max), invia `tts_start`, chunk binari da `2048` byte PCM16 e `tts_end`.
4. **Riproduzione ESP32 I²S (`04-Firmware/arduino-hw-test/jarvis_wifi_voice_client/audio_playback.cpp`, `.h`)**:
   - Il task FreeRTOS `jarvis_audio_tx` (Core 0, Prio 3) legge da `AudioBuffer` (già interamente ricevuto prima di `Start()`), applica volume (`12%`) e fade-in/out lineare di `320` frame (`20 ms`), duplica in stereo e scrive su `I2S_NUM_1` (`16000 Hz`, 16 bit) a blocchi di `256` frame (`16 ms`), chiudendo con `960` frame (`60 ms`) di zeri (`WriteZeroFlush`).

---

## 2. Differenze reali tra i profili testati

Tutti i 6 profili partono dallo **stesso WAV grezzo generato da Piper** (`1.00x`, `noise_scale=1.10`) per isolare esclusivamente l'effetto di ciascuno stadio DSP:

| Profilo | Pitch | DSP / Limiter | Metodo Pitch Shifting | Scopo diagnostico |
| :--- | :--- | :--- | :--- | :--- |
| **A** | `0` st | **Off** (solo `validate_and_normalize_wav`) | Nessuno | Baseline puro Piper `x_low` a `1.00x` |
| **B** | `0` st | **On** (`shape_piper_wav` -> `active_rms` + `tanh`) | Nessuno (`abs(0) < 0.05`) | Isolare l'effetto del solo compressore/limiter `tanh` |
| **C** | `+3` st | **On** (`shape_piper_wav` completo) | Phase vocoder STFT `1024/256` + `tanh` | Valutare pitch intermedio con DSP attuale |
| **D (LIVE)** | `+5` st | **On** (`shape_piper_wav` completo) | Phase vocoder STFT `1024/256` + `tanh` | Riferimento configurazione live FASE 12.21 |
| **E** | `+5` st | **No `tanh`** (normalizzazione lineare peak `-1 dBFS` / `0.89`) | Phase vocoder STFT `1024/256` | Isolare il phase vocoder `+5` dal compressore `tanh` |
| **F** | `+5` st | **No `tanh`** (normalizzazione lineare peak `-1 dBFS` / `0.89`) | WSOLA time-domain (`24 ms` Hann, `6 ms` hop, pure-NumPy) | Alternativa time-domain al phase vocoder STFT |

*(Nota su F: nell'ambiente `.venv` locale è presente `numpy 2.5.4`, mentre `scipy`, `librosa`, `soundfile`, `ffmpeg`, `sox` e `rubberband` non sono installati. Per fornire un confronto time-domain reale senza installare librerie, è stato implementato un WSOLA pure-NumPy nello script diagnostico isolato.)*

---

## 3. Risultati del benchmark comparativo

Tempo sintesi grezza Piper (`1.00x`, `11.84 s` di parlato): **`1364.8 ms`**.

| Profilo | Durata (s) | PCM (byte) | Peak (dBFS) | Active RMS (dBFS) | Crest Factor (dB) | Clipping / `>=0.95` | Silenzio iniziale / finale (ms) | Max jump / salti `>0.30` | Energia 4–8 kHz (%) | Env. Mod. CV (10 ms) | Tempo DSP (ms) |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **A** (Piper puro) | 11.840 | 378.880 | -0.00 | -12.70 | **12.70** | 4 / 22 | 52.6 / 438.0 | 0.7429 / 492 | 0.38% | **0.647** | 52.7 |
| **B** (Solo `tanh`) | 11.840 | 378.880 | -0.59 | -8.64 | **8.05** | 0 / 0 | 52.6 / 437.9 | 1.2517 / **2102** | 0.53% | 0.585 | 54.5 |
| **C** (`+3` DSP att.) | 11.826 | 378.444 | -0.42 | -8.75 | 8.32 | 0 / 5 | 0.6 / 404.5 | 0.9198 / 1721 | 0.36% | 0.546 | 139.4 |
| **D** (`+5` LIVE) | 11.819 | 378.196 | -0.43 | -8.77 | 8.34 | 0 / 6 | **0.5** / 397.6 | 1.0350 / **2617** | 0.53% | **0.533** | 148.3 |
| **E** (`+5` no `tanh`) | 11.819 | 378.196 | -1.01 | -15.78 | **14.77** | 0 / 0 | **0.5** / 403.9 | 0.3844 / **29** | 0.39% | 0.606 | 150.7 |
| **F** (`+5` WSOLA) | 11.840 | 378.880 | -1.01 | -13.87 | **12.86** | 0 / 0 | 49.8 / 440.8 | 0.5940 / 263 | 0.29% | **0.658** | 1924.4 |

---

## 4. Anomalie confermate vs ipotesi da verificare all'ascolto

### Anomalie oggettivamente confermate dalle misure
1. **Compressione dinamica aggressiva da `tanh` (B, C, D)**: `shape_piper_wav` applica un guadagno ~`2.07x` seguito da saturazione `tanh`, riducendo il *crest factor* da **`12.70 dB`** (A) a **`8.05–8.34 dB`** (B, C, D) e moltiplicando i salti campione-campione `> 0.30` da `492` (A) a `2102` (B) e `2617` (D). Ciò appiattisce i picchi consonantici rispetto alle vocali adiacenti e alza le code di rumore/respiro.
2. **Spalmatura temporale del phase vocoder da `64 ms` (`n_fft=1024`)**: l'indice di modulazione dell'inviluppo (`Env. Mod. CV` su frame da `10 ms`) scende da **`0.647`** (A) a **`0.606`** (E, solo vocoder) fino a **`0.533`** (D, vocoder + `tanh`), che è il valore più appiattito dell'intero test. Inoltre, la finestra STFT da `64 ms` anticipa il primo attacco vocale azzerando il silenzio iniziale da `52.6 ms` (A) a `0.5 ms` (D, E).
3. **Effetto combinato D vs A/E/F**: la configurazione live (D) somma entrambi gli effetti (phase vocoder `64 ms` + compressione `tanh`), producendo il minimo contrasto d'inviluppo (`0.533`) e il massimo numero di transizioni ripide non lineari (`2617` salti `> 0.30`).
4. **WSOLA time-domain (F)** preserva sia il *crest factor* (`12.86 dB` vs `12.70 dB` di A), sia il silenzio iniziale (`49.8 ms` vs `52.6 ms`), sia la modulazione dell'inviluppo (`0.658` vs `0.647`), ma nella versione non vettorizzata richiede ~`1.92 s` di CPU per `11.84 s` di audio.

### Ipotesi da verificare all'ascolto dell'utente
- **Se in A (Piper puro) le parole risultano già leggermente impastate**: la causa principale è a monte del DSP (modello `it_IT-riccardo-x_low` a 16 kHz con sola energia 4–8 kHz dello `0.38%` e/o `noise_scale=1.10`).
- **Se A e B sono chiari ma D impasta**: il colpevole principale è il phase vocoder `n_fft=1024` a `+5` semitoni (verificabile confrontando D/E con C e F).
- **Se A/E sono più nitidi di B/D**: la saturazione `tanh` sta degradando l'articolazione delle consonanti.

---

## 5. Percorsi dei file WAV generati

Cartella: `05-Voice-AI/tts-lab/samples_fase12_22/`

- **A — Baseline puro Piper**: `05-Voice-AI/tts-lab/samples_fase12_22/A_baseline_puro_piper_1.00x_pitch0_nodsp.wav`
- **B — Solo livello / `tanh` (pitch 0)**: `05-Voice-AI/tts-lab/samples_fase12_22/B_solo_tanh_1.00x_pitch0_dsp.wav`
- **C — Pitch +3 con DSP attuale**: `05-Voice-AI/tts-lab/samples_fase12_22/C_pitch_plus3_1.00x_dsp_attuale.wav`
- **D — Pitch +5 con DSP attuale (LIVE)**: `05-Voice-AI/tts-lab/samples_fase12_22/D_pitch_plus5_1.00x_dsp_attuale_live.wav`
- **E — Pitch +5 phase vocoder senza `tanh`**: `05-Voice-AI/tts-lab/samples_fase12_22/E_pitch_plus5_1.00x_vocoder_no_tanh.wav`
- **F — Pitch +5 WSOLA time-domain senza `tanh`**: `05-Voice-AI/tts-lab/samples_fase12_22/F_pitch_plus5_1.00x_wsola_no_tanh.wav`

---

## 6. Diagnostica firmware ESP32 I²S (`audio_playback.cpp`, `audio_playback.h`)

Verifica in sola lettura del task I²S sul firmware ESP32:
- **Sample rate e formato**: `kSampleRateHz = 16000U`, `I2S_DATA_BIT_WIDTH_16BIT`, `I2S_SLOT_MODE_STEREO` (campione mono duplicato su L/R). Coerente al 100% con il PCM16 a 16 kHz inviato dal Voice Bridge.
- **Dimensioni chunk e timing**: chunk da `kChunkFrames = 256` frame (`16 ms`), fade-in e fade-out da `kFadeFrames = 320` frame (`20 ms`) — non taglia parole ma ammorbidisce i primi/ultimi 20 ms — più flush finale di `960` frame (`60 ms`) di silenzio.
- **Buffer / underrun**: `AudioPlayback::Start(buffer)` riproduce un `AudioBuffer` già completo in memoria; quindi durante il parlato non ci sono underrun dovuti alla rete Wi-Fi. Inoltre il firmware misura attivamente `i2s_errors_`, `partial_writes_`, `max_write_us_`, `inter_gt_30ms_` e `inter_gt_90ms_`.
- **Osservazione marginale sul codice (`audio_playback.cpp`, righe 303–316)**: se `i2s_tx_.write()` restituisse una scrittura parziale (`written != bytes_to_write`), `partial_writes_` verrebbe incrementato ma `idx_base += n` avanzerebbe comunque dell'intero blocco senza ritentare i byte residui. Con il driver `ESP_I2S` bloccante in condizioni normali `partial_writes_` resta `0`, ma in caso di saturazione DMA/errori causerebbe micro-salti; il firmware non è stato modificato.

---

## 7. Raccomandazione tecnica (da confermare dopo ascolto)

1. **Non modificare nulla finché l'utente non ha ascoltato i 6 campioni**.
2. Dalle misure oggettive, l'attuale profilo live **D** soffre di una combinazione di **spalmatura temporale (`n_fft=1024`, 64 ms)** e **compressione `tanh` (`-4.4 dB` di crest factor)**.
3. Se all'ascolto **E** o **F** risultano molto più intelligibili di **D**, l'intervento più pulito sarà sostituire/attenuare la compressione `tanh` (usando normalizzazione lineare/picco sicuro invece di `gain=2.07x + tanh`) e, se confermato dal confronto **E vs F** (o **C vs D**), passare a pitch `+3`/WSOLA o a una finestra vocoder più corta.
4. Se invece anche **A** dovesse risultare impastato all'ascolto, il passo successivo sarà diagnosticare i parametri nativi Piper (`noise_scale=0.667` vs `1.10`) o un modello alternativo.

---

## 8. Scelte aperte per l'utente

Ascoltare i 6 file WAV in `05-Voice-AI/tts-lab/samples_fase12_22/` (in particolare confrontare **A vs B**, **D vs E**, **E vs F** e **C vs D**) e indicare:
1. Quale campione (**A, B, C, D, E, F**) risulta più chiaro e naturale all'orecchio?
2. Nel campione **A** (Piper puro, senza DSP) le parole si sentono ancora "mangiate", oppure diventano nitide?
