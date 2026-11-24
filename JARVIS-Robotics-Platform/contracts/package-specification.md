# Specifiche dei Pacchetti di Risorse e Sicurezza Archivi

> **JARVIS Robotics Platform** — Standard di Packaging, Integrità e Sicurezza  
> **Fase:** RP-02  
> **Stato:** Approvato per Progettazione  

---

## 1. Visione d'Insieme dei Formati di Pacchetto

La piattaforma definisce tre formati di archivio standardizzati:
- **`.jarvis-skin`:** Pacchetto contenente la definizione geometrica, le maschere bitmap e i parametri di animazione di una skin oculare.
- **`.jarvis-identity`:** Pacchetto contenente l'intera identità logica (system prompt, stile, riferimenti a voce e wake word, saluti).
- **`.jarvis-hardware`:** Descrittore formale della configurazione elettronica, pinout e limiti di sicurezza del robot fisico.

Ciascun pacchetto è fisicamente un **archivio ZIP conforme alle specifiche PKWARE (metodo di compressione Deflate standard)**, contenente un file manifesto formale `manifest.json` posizionato alla radice dell'archivio.

---

## 2. Struttura Interna degli Archivi

```
+---------------------------------------------------------------------------------+
| ARCHIVIO .jarvis-skin                                                           |
+---------------------------------------------------------------------------------+
| /manifest.json          [Obbligatorio: conforme a package.schema.json]          |
| /skin.json              [Obbligatorio: conforme a skin.schema.json]             |
| /assets/                [Opzionale: maschere monocromatiche 1-bit in formato XBM]|
|   └── mask_heart.xbm                                                            |
|   └── mask_hud_ring.xbm                                                         |
+---------------------------------------------------------------------------------+

+---------------------------------------------------------------------------------+
| ARCHIVIO .jarvis-identity                                                       |
+---------------------------------------------------------------------------------+
| /manifest.json          [Obbligatorio: conforme a package.schema.json]          |
| /identity.json          [Obbligatorio: conforme a identity.schema.json]         |
| /prompts/                                                                       |
|   └── system_prompt.md  [Opzionale: testo esteso del prompt di sistema]         |
| /sounds/                                                                        |
|   └── chime.wav         [Opzionale: effetto acustico WAV 16kHz mono]            |
+---------------------------------------------------------------------------------+
```

---

## 3. Politiche Rigide di Sicurezza nell'Estrazione Archivi

Per proteggere l'infrastruttura host (Raspberry Pi 5 / PC Windows) da pacchetti malevoli o alterati, l'importatore di JARVIS Identity Studio implementa i seguenti controlli tassativi prima di qualsiasi estrazione:

### 3.1 Protezione da Path Traversal (Attacco Zip-Slip)
- Ogni entry name contenuto nell'archivio viene normalizzato e ispezionato prima della scrittura su disco.
- **Rifiuto Tassativo:** È categoricamente respinto qualsiasi file il cui percorso contenga la sequenza `../` o `..\`, inizi con una barra `/` o contenga lettere di unità (es. `C:`).
- L'estrazione avviene rigorosamente all'interno di una cartella temporanea sandbox con percorso verificato (`os.path.commonpath([base_dir, target_file]) == base_dir`).

### 3.2 Protezione da Zip-Bomb (Denial of Service)
- **Rapporto di Compressione Massimo:** Se il rapporto tra dimensione decompressa e dimensione compressa eccede **10:1**, l'estrazione viene interrotta istantaneamente.
- **Tetto Massimo Decompresso:**
  - Pacchetto `.jarvis-skin`: Max **`256 KB`** estratti totali.
  - Pacchetto `.jarvis-identity`: Max **`512 KB`** estratti totali.
  - Pacchetto `.jarvis-hardware`: Max **`64 KB`** estratti totali.
- **Numero Massimo di File:** Massimo **25 elementi** totali per archivio.
- **Divieto di Archivi Annidati:** Gli archivi ZIP non possono contenere altri file compressi al loro interno (`.zip`, `.tar`, `.gz`).

### 3.3 Divieto Assoluto di File Eseguibili e Symlink
- **Rifiuto Symlink / Hardlink:** Qualsiasi entry con attributi POSIX di collegamento simbolico o hardlink provoca il rigetto immediato del pacchetto.
- **Rifiuto Eseguibili:** L'archivio può contenere unicamente estensioni dichiarate ammesse (`.json`, `.xbm`, `.wav`, `.md`, `.tflite`). È bloccata qualsiasi presenza di file eseguibili o script (`.bin`, `.elf`, `.exe`, `.py`, `.sh`, `.bat`, `.lua`, `.wasm`, `.so`, `.dll`).

---

## 4. Integrità Crittografica vs Autenticità d'Autore

La piattaforma distingue rigorosamente i due concetti di sicurezza:

### 4.1 Checksum di Integrità (SHA-256)
- Il file `manifest.json` elenca ciascun file contenuto nell'archivio associato al suo hash SHA-256 esadecimale.
- Al momento dell'importazione, il validatore calcola l'hash dei file estratti: se anche un solo bit differisce, l'importazione fallisce con errore `INTEGRITY_MISMATCH`.
- *Nota di rigore:* Un checksum SHA-256 garantisce l'integrità contro la corruzione accidentale, **ma non certifica l'identità dell'autore** né costituisce una firma digitale.

### 4.2 Firma Digitale di Autenticità (Asimmetrica Ed25519)
- I pacchetti ufficiali rilasciati dalla piattaforma includono una firma crittografica asimmetrica opzionale (`signature` nel manifesto) generata con chiave privata Ed25519.
- JARVIS Identity Studio verifica la firma contro le chiavi pubbliche fidate memorizzate nella cartella di configurazione, segnalando chiaramente all'utente se il pacchetto proviene dal team ufficiale o da terze parti non verificate.
