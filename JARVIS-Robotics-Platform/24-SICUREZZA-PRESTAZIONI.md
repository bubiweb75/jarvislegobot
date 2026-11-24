# 24 — Sicurezza, Affidabilità e Prestazioni

> **JARVIS Robotics Platform** — Budget Risorse, Sicurezza e Vincoli Operativi  
> **Fase:** RP-01  
> **Stato:** Approvato per Progettazione  

---

## 1. Principi di Sicurezza e Affidabilità

La **JARVIS Robotics Platform** pone la sicurezza fisica dell'hardware, l'integrità dei dati e l'affidabilità deterministica del microcontrollore al di sopra di qualsiasi funzionalità opzionale o estetica.

Principi architetturali fondamentali:
1. **Isolamento dei Guasti:** Il malfunzionamento di una componente non critica (es. errore di parsing di una nuova skin o timeout del server AI) non deve **mai causare il blocco o il reset del microcontrollore**, né compromettere i compiti di sicurezza o il funzionamento del pulsante fisico PTT.
2. **Indipendenza delle Funzioni di Movimento:** Per i robot dotati di base mobile (*Mobile V2*), il controllo dei motori e i sensori anti-caduta risiedono in un task prioritario isolato. La personalità, la voce o le animazioni grafiche non hanno alcuna autorità per forzare movimenti non sicuri o bypassare i sensori cliff.
3. **Modalità di Emergenza e Ripristino di Fabbrica (Safe Boot):** In caso di crash ripetuti al boot, il firmware attiva automaticamente la configurazione di sicurezza, caricando l'identità certificata **JARVIS Original Premium** e disattivando le configurazioni custom non validate.

---

## 2. Budget Rigoroso delle Risorse Hardware (ESP32-S3 N16R8)

La tabella seguente riporta i vincoli di budget verificati strumentalmente sui collaudi delle Fasi 10.3, 12.27 e 13.7:

| Risorsa Hardware | Capacità Fisica Totale | Limite di Budget Assegnato | Consumo Effettivo Misurato (FASE 13.7) | Margine Libero Garantito | Note di Conformità |
|---|---|---|---|---|---|
| **Flash SPI (Programma)** | `16 MB` (`16.777.216 B`) | `1.310.720 B` (`app0`) | `1.299.328 B` (`99,1%`) | `11.392 B` | Pienamente operativo; consigliata partizione `app0` da 3 MB per estensioni future. |
| **SRAM Interna (Heap)** | `512 KB` (`524.288 B`) | Minimo Heap > `80 KB` | `129.252 B` a regime | `> 120 KB` | Zero memory leak su oltre 10 minuti continui di stress vocale. |
| **Octal PSRAM (OPI)** | `8 MB` (`8.388.608 B`) | `3.000.000 B` | `1.536.000 B` (`18,3%`) | **`~6.787.000 B` (`81,7%`)** | Ampio spazio residuo per buffer audio, cache skin e future espansioni. |
| **Stack Task Audio (Core 0)**| `12.288 B` | HWM > `2.048 B` | `10.036 B` liberi (`81,7%`) | `10.036 B` | Margine eccellente per prevenire stack overflow. |
| **Stack Task Grafico (Core 1)**| `8.192 B` | HWM > `1.500 B` | `5.840 B` liberi (`71,3%`) | `5.840 B` | Margine sicuro per il loop di rendering U8g2. |

---

## 3. Budget Prestazionali e Latenze della Pipeline

Per garantire un'interazione uomo-robot naturale, reattiva e priva di ritardi fastidiosi, la piattaforma definisce i seguenti tempi limite (*latency targets*):

```mermaid
flowchart LR
    WAKE["1. Wake Word<br>(<= 120 ms)"] --> NET_UP["2. Upload Audio<br>(<= 40 ms)"]
    NET_UP --> STT["3. STT Whisper<br>(<= 300 ms)"]
    STT --> LLM["4. LLM Reasoning<br>(<= 1200 ms)"]
    LLM --> TTS["5. TTS Piper<br>(<= 200 ms)"]
    TTS --> NET_DOWN["6. Stream Down<br>(<= 30 ms)"]
    NET_DOWN --> SPK["7. Playback I2S<br>(<= 10 ms)"]

    style WAKE fill:#1e293b,stroke:#38bdf8,stroke-width:2px;
    style SPK fill:#1e293b,stroke:#22c55e,stroke:#width:2px;
```

### 3.1 Dettaglio delle Latenze Obiettivo

| Fase della Pipeline | Componente Responsabile | Latenza Obiettivo (Target V1) | Risultato Misurato (FASE 13.7) |
|---|---|---|---|
| **Rilevamento Wake Word** | ESP32-S3 (microWakeWord INT8) | ≤ `150 ms` | **`~110 ms`** |
| **Chiusura VAD dopo Silenzio** | ESP32-S3 (Holdoff dinamico) | ≤ `350 ms` | **`~300 ms`** |
| **Trascrizione Vocale (STT)** | Host RPi5 (Faster-Whisper base) | ≤ `350 ms` | **`210 – 320 ms`** |
| **Elaborazione Cognitiva (LLM)** | Host RPi5 (Ollama qwen2.5:3b) | ≤ `1.500 ms` | **`800 – 1.400 ms`** (Intenti locali: **`15 ms`**) |
| **Sintesi Vocale (TTS)** | Host RPi5 (Piper TTS + WSOLA) | ≤ `250 ms` | **`140 – 190 ms`** |
| **Avvio Riproduzione Audio** | ESP32-S3 (Buffer I2S Core 0) | ≤ `30 ms` | **`< 15 ms`** |
| **TEMPO TOTALE END-TO-END** | **Dalla fine domanda al primo suono** | **≤ `2.500 ms`** | **`1.850 – 2.450 ms`** (Pienamente conforme) |

### 3.2 Prestazioni del Display Oculare (Eyes Engine)
- **Frame Rate Minimo Garantito:** **`30 FPS stabili`** (intervallo frame `33,3 ms`).
- **Tempo di Calcolo Framebuffer (CPU):** ≤ `2,8 ms` (inferiore al 9% del tempo disponibile).
- **Tempo di Trasferimento Bus I2C (SH1106):** `24,2 ms` @ 400 kHz.
- **Frame Droppati Tollerati:** `0 frame persi` durante la normale animazione in `IDLE`.

---

## 4. Protezioni Elettroniche e Sicurezza Meccanica

### 4.1 Protezione dei Pin Critici dell'ESP32-S3
- **Pin Strapping Boot:** `GPIO 0, 3, 45, 46` non sono collegati a carichi esterni che possano alterarne lo stato al momento del boot. In particolare, `GPIO 45` è rigorosamente non collegato (`NC`) per scongiurare la selezione errata del rail PSRAM a 1.8V anziché 3.3V.
- **Pin Octal PSRAM:** `GPIO 35, 36, 37` sono fisicamente isolati e vietati da qualsiasi assegnazione software.

### 4.2 Sicurezza della Base Mobile 2WD (Profilo Mobile V2)
1. **Watchdog di Movimento su Bus Seriale:** Un timer hardware spegne i ponti H del chip TB6612FNG se non viene ricevuto un comando di mantenimento velocità valido per più di **500 ms**.
2. **Priorità Assoluta Sensori Anti-Caduta (Cliff Sensors):** La lettura dei sensori IR frontali ha la precedenza assoluta su qualunque richiesta software o script AI. L'assenza del piano di calpestio avvia la sequenza di sicurezza:
   - Tempo di rilevamento ottico IR: ≤ 2 ms.
   - Tempo di elaborazione interrupt MCU: ≤ 1 ms.
   - Tempo di disabilitazione driver (ponte H in modalità `BRAKE` attivo, cortocircuito avvolgimenti, seguito da `STBY = LOW`): ≤ 2 ms.
   - Tempo di arresto elettrico: arresto della rotazione attiva in ≤ 15 ms.
   - Arresto meccanico effettivo: decelerazione inerziale dipendente dalla velocità e dal coefficiente di attrito ruota-suolo (spazio di arresto stimato tra 5 e 20 mm).
   - **Prescrizione Operativa:** Nei collaudi a banco su tavolo o scrivania è obbligatorio l'uso di barriere fisiche di contenimento o supporto ruote sollevate (*wheels-up*), senza fare affidamento esclusivo sul solo sensore per scongiurare cadute.
3. **Massa Comune a Stella e Filtraggio Antidisturbo Motori:** I circuiti condividono un piano di massa di riferimento comune unito a stella (non isolamento galvanico). I motori N20 sono alimentati direttamente dal pacco batteria 2S attraverso filtri LC dedicati e diodi di soppressione, mentre la logica di controllo opera a 3.3V a valle del regolatore Buck, eliminando reset indotti da disturbi a spazzola.

---

## 5. Privacy dei Dati e Tutela dell'Utente

1. **Assenza di Registrazione Continua:** Il flusso audio del microfono INMP441 transita unicamente attraverso il buffer volatile circolare dell'inferenza wake word locale. Nessun dato audio viene memorizzato su memoria Flash o inviato alla rete prima del rilevamento convalidato della parola chiave.
2. **Nessun Modello Vocale o Chiave Inviata a Cloud Esterni:** Nella configurazione standard della piattaforma, tutta la trascrizione (STT), l'elaborazione linguistica (LLM) e la sintesi (TTS) avvengono localmente su Raspberry Pi 5 all'interno della LAN domestica protetta.
3. **Cancellazione Istantanea:** L'utente può azzerare in qualsiasi momento la cronologia o i log vocali di ciascun robot direttamente dalla dashboard di Identity Studio.
