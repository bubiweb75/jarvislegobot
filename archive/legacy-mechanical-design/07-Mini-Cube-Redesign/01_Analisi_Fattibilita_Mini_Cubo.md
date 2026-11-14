# 01 – Analisi di Fattibilità del Mini Cubo (FASE A)

**Obiettivo:** Verificare la fattibilità meccanica, geometrica ed elettronica del redesign di **JARVIS LEGO BOT** in formato **Mini Cubo** (`~80 × 80 × 90–96 mm`), con OLED `1,3" SH1106` frontale (volto digitale) e speaker sul tetto, senza avviare modellazione LDraw o acquisti prima dell'approvazione.

---

## 1. Audit dei Documenti Esistenti: Cosa Restano Valido vs Cosa È Superato

### 1.1 Decisioni tecniche conservate (valide)
- **Elettronica e pinout (`01-Hardware/02_Tabella_Pinout_Definitiva.md`):**
  - `ESP32-S3-DevKitC-1 N16R8`, `INMP441` (`GPIO 4/5/6`), `MAX98357A` (`GPIO 7/15/16`), `OLED SH1106 1,3"` (`GPIO 41/42`), pulsante NO (`GPIO 47`), connettore `JST-XH 6-pin` (`GPIO 17/18` UART + `GPIO 8/9` I2C + `5V/GND`).
  - Esclusioni pin (`GPIO 35–37` Octal PSRAM, `GPIO 3/45/46` strapping, `GPIO 39/40` disabilitati, `J1-3` `RST` mai a GND).
- **Sicurezza alimentazione (`01-Hardware/01_Schema_Elettronico_e_Alimentazione.md` e `05-Mobile-Electronics/`):**
  - Distribuzione a stella `5V` + `C1 (470 µF)` + `C2 (100 nF)` su `MAX98357A`, diodi `D1/D7` (`1N5819HW-7-F`), anti-backfeed `LM66100` su B2, divieto alimentazione simultanea USB-C PC + `5V` esterno / B2.
- **Architettura software (`docs/`):** `78/xiaozhi-esp32` su ESP32-S3 + backend AI su Raspberry Pi 5 in LAN.
- **Modularità `A ↔ B1 / B2`:** corpo A trasferibile su base fissa B1 o futura base mobile B2 senza smontare l'elettronica interna.
- **Lezioni CAD LDraw (`06-LEGO-Buildability-Audit/08_Correzione_Collisioni_Studio.md`):** uso di mesh reali `.dat` di BrickLink Studio 2.0 per assi liftarm/ruote, offset SNOT `87087`, cerniere e sportelli.

### 1.2 Decisioni superate dal Redesign Mini Cubo
| Elemento | Progetto precedente (`jarvis_lego_bot.mpd`, `184` pz) | Nuova decisione Mini Cubo |
|---|---|---|
| **Proporzioni Corpo A** | `10 × 10 × 15 brick` (`80 × 80 × 144 mm`, aspetto a torre) | **`10 × 10 × 10 brick` (`80 × 80 × 96,0 mm`)** (o `9b+1p = 89,6 mm` se speaker slim) |
| **Posizione Speaker** | Frontale basso dietro griglia SNOT `6×6` | **Sul tetto, rivolto verso l'alto** sotto griglia LEGO removibile |
| **Ruolo Frontale** | Speaker basso + piccola finestra OLED superiore (`6×4` con cerniere `3937/3938`) | **Dominato dal display OLED `1,3" SH1106`** (volto digitale di JARVIS) |
| **Posizione Pulsante `GPIO 47`** | Frontale tra speaker e OLED (`14769` Azure) | **Sul fianco** del corpo A (mantiene frontale pulito) |
| **Posizione Microfono `INMP441`** | Frontale alto sopra OLED (`3700`) | **Lato o angolo superiore**, meccanicamente isolato dal tetto speaker |
| **Setto interno** | Setto orizzontale rigido a `Z = 83,2 mm` | **Sostituito da culla/camera acustica superiore compatta** per liberare altezza utile |

---

## 2. Verifica Sintetica di Fattibilità sui Vincoli Dimensionali

- **Ingombro esterno obiettivo:** `80 × 80 × 90 mm` (accettabile `85–100 mm` in altezza).
- **Griglia LEGO reale (`1 stud = 8,0 mm`, `1 brick = 9,6 mm`, `1 plate = 3,2 mm`):**
  - `10 × 10 stud` = **`80,0 × 80,0 mm`** → con pareti da `1 stud` (`8,0 mm`), vano interno netto = **`64,0 × 64,0 mm`** (`8 × 8 stud`).
  - Altezza **`10 brick` (`30 plate`) = `96,0 mm`** (rientra pienamente nell'obiettivo `85–100 mm`, rapporto `1 : 1 : 1,20`).
  - Altezza **`9 brick + 1 plate` (`28 plate`) = `89,6 mm`**: possibile **solo** adottando uno speaker slim (`spessore ≤ 14–15 mm`), mentre con lo speaker `Ø 40 × 20 mm` i `96,0 mm` (`10 brick`) garantiscono i margini necessari per connettori e cavi.
- **Base fissa B1:** `12 × 11 stud` (`96 × 88 mm`) o `12 × 12 stud` (`96 × 96 mm`), sporgenza esterna sottile `1–2 plate` (`3,2–6,4 mm`) → **altezza complessiva `99,2 – 102,4 mm`** (pienamente nell'obiettivo `100–115 mm`).

---

## 3. Verdetto di Fattibilità (FASE A)

**FATTIBILE — CON CONFIGURAZIONE RACCOMANDATA `LAYOUT C` + CORPO `80 × 80 × 96,0 mm` (`10 × 10 stud × 10 brick`).**

Condizioni chiave per garantire montabilità e manutenzione reali senza forzare cavi/connettori:
1. Adottare il **Layout C** (`ESP32-S3` verticale decentrato nell'angolo posteriore, `OLED 1,3"` incassato nel frontale, speaker sul tetto decentrato sul quadrante libero).
2. Utilizzare **connettori a profilo basso** (header a 90° o saldatura diretta con cavi silicone `26 AWG` + connettori inline compatti) su `ESP32-S3`, `OLED` e `INMP441`.
3. Confermare le quote esatte di ingombro della **PCB commerciale OLED `1,3" SH1106`** e della **profondità reale dello speaker `4 Ω / 3 W`** prima di finalizzare i supporti in FASE B (nel frattempo viene usato un inviluppo parametrico prudenziale).
