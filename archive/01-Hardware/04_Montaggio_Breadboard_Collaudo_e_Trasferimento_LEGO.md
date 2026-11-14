# Elaborati E, F & G – Montaggio Breadboard, Trasferimento LEGO e Test Pre-Alimentazione

**Progetto:** JARVIS LEGO BOT – FASE 2

---

## Elaborato E – Schema di Montaggio su Breadboard (Primo Collaudo)

### E.1 Disposizione Fisica Consigliata
Poiché la **ESP32-S3-DevKitC-1** ha una larghezza di ~25,4 mm (10 passi da 2,54 mm tra le due file di pin `J1` e `J3`):
1. Inserire la DevKitC-1 a cavallo del canale centrale della breadboard (o a cavallo tra **due breadboard affiancate** per avere più fori liberi per lato).
2. Predisporre i binari laterali della breadboard:
   - **Binario superiore (Rosso/Blu):** **`+3,3 V`** e **`GND`** (collegati a `3V3` [`J1-1` o `J1-2`] e `GND` [`J1-22` / `J3-1`]).
   - **Binario inferiore (Rosso/Blu):** **`+5 V`** e **`GND`** (nodo comune a stella).
3. **Posizionamento moduli:**
   - **Lato sinistro:** `INMP441` (lontano dallo speaker per evitare feedback) e `OLED 1,3"`.
   - **Lato destro:** `MAX98357A` con **`C1` (470 µF)** e **`C2` (100 nF)** inseriti direttamente nei fori adiacenti a `VIN` e `GND` (fascia `-` di `C1` su `GND`).
   - **Zona frontale:** `Pulsante NO` a cavallo del canale centrale, un lato a `GND`, l'altro a `GPIO 47` (`J3-17`).

### E.2 Sequenza di Cablaggio su Breadboard
1. **Masse comuni:** Collegare `GND` DevKitC-1 (`J1-22` e `J3-1`/`J3-21`/`J3-22`) al binario `GND` inferiore e ponticellare con il binario `GND` superiore. **Non collegare `J1-3` (`RST/EN`) a `GND`!**
2. **Rail 3,3 V:** Collegare `3V3` (`J1-1`) al binario `+3,3 V` superiore.
3. **Filtraggio audio:** Inserire `C1` (470 µF, `+` su `+5V`, `-` su `GND`) e `C2` (100 nF) nella zona del `MAX98357A`.
4. **INMP441:** `VDD → +3,3V`, `GND → GND`, `L/R → GND`, `WS → GPIO 4` (`J1-4`), `SCK → GPIO 5` (`J1-5`), `SD → GPIO 6` (`J1-6`).
5. **OLED 1,3":** Verificare prima l'ordine dei pin serigrafato sul PCB! Poi `VCC → +3,3V`, `GND → GND`, `SDA → GPIO 41` (`J3-7`), `SCL → GPIO 42` (`J3-6`).
6. **MAX98357A:** `VIN → +5V` (binario inferiore, **MAI da `3V3`**), `GND → GND`, `SD → +3,3V`, `DIN → GPIO 7` (`J1-7`), `BCLK → GPIO 15` (`J1-8`), `LRC → GPIO 16` (`J1-9`), `OUT+/OUT- → Speaker 4Ω/3W`.
7. **Pulsante:** Pin A → `GPIO 47` (`J3-17`), Pin B → `GND`.
8. **Scelta modalità di alimentazione prima di accendere:**
   - **Modalità B (Flash/Debug da PC):** Lasciare **scollegato** il breakout USB-C esterno dal binario `+5V` (non collegare il breakout mentre la DevKitC-1 è attaccata al PC; per i primi test senza audio ad alto volume `J1-21` non deve ricevere alimentazione esterna).
   - **Modalità A (Funzionamento autonomo):** A PC scollegato, collegare il breakout USB-C 5 V (≥ 2 A) al binario `+5V`/`GND`, che alimenta a stella `J1-21` (`5V` DevKitC-1) e `VIN` del MAX98357A.

---

## Elaborato F – Indicazioni per il Trasferimento nella Struttura LEGO

1. **Modularità:** Usare connettori **JST-XH** o pettini DuPont bloccati con guaina termorestringente, così da poter estrarre singolarmente testa (OLED + Mic) o elettronica dal pannello posteriore LEGO.
2. **Separazione Testa / Corpo:**
   - **Testa:** OLED 1,3" frontale + INMP441 dietro foro acustico disaccoppiato con spugna/gommapiuma. Fascio ordinato di **7 fili flessibili 26 AWG** verso il corpo (`3V3`, `GND`, `SDA`, `SCL`, `WS`, `SCK`, `SD` mic).
   - **Corpo:** DevKitC-1 accessibile dal retro (porta USB-C raggiungibile, antenna lontana da speaker e cavi audio), speaker 4 Ω / 3 W verso griglia frontale/laterale, MAX98357A + `C1`/`C2` + breakout USB-C 5 V fissati nel vano inferiore/posteriore. **Prevedere feritoie di ventilazione passiva** (ingresso aria inferiore + sfogo superiore/posteriore) per mantenere $T_A$ interna attorno all'LDO della DevKitC-1 sotto i ~35 °C.
3. **Predisposizione base mobile futura:** Mantenere liberi `GPIO 1, 2, 8–14, 17, 18, 21` e lasciare spazio nella base per futuri motori/driver.

---

## Elaborato G – Checklist Test Prima di Alimentare il Circuito

Eseguire **tutti** i controlli **a circuito completamente scollegato da qualsiasi USB/alimentatore**, con multimetro in modalità **continuità (buzzer)** e **resistenza (Ω)**:

1. **Cortocircuiti sulle Linee di Alimentazione:**
   - Misurare tra **`+5V` (`J1-21`) e `GND` (`J1-22`)**: nessun beep continuo / resistenza alta dopo la carica di `C1`.
   - Misurare tra **`+3,3V` (`J1-1`) e `GND`**: nessun corto.
   - Misurare tra **`+5V` e `+3,3V`**: nessun corto tra i due rail.
2. **Verifica Pin Critici DevKitC-1:**
   - Confermare che **`J1-3` (`RST/EN`) NON sia collegato a `GND`**.
   - Confermare che **`J1-21` (`5V`)** sia l'unico pin della DevKitC-1 collegato al ramo `+5V` (e **non** `J3-21`, che è `GND`).
   - Confermare che **`GPIO 35, 36, 37`** e **`GPIO 39, 40`** siano completamente scollegati.
3. **Verifica Polarità e Moduli:**
   - **OLED 1,3":** verificare serigrafia `VCC` → `3,3V` e `GND` → `GND`.
   - **INMP441:** `VDD` → **`3,3V`** (mai 5 V) e `L/R` → `GND`.
   - **MAX98357A:** `VIN` → `5V` (mai `3V3`), `SD` → `3,3V`, speaker **esclusivamente tra `OUT+` e `OUT-`** (nessun polo a `GND`).
   - **Condensatore `C1` (470 µF):** terminale negativo (`-`) su `GND`, positivo su `+5V`.
4. **Test Pulsante (`GPIO 47` / `J3-17`):**
   - A riposo tra `GPIO 47` e `GND`: circuito aperto (`OL`). Premuto: continuità (`~0 Ω`).
5. **Controllo Speaker:**
   - Resistenza tra `OUT+` e `OUT-` a circuito spento: ~3,5 – 4,5 Ω.
6. **Verifica Modalità Alimentazione & Primo Avvio ("Smoke Test"):**
   - Verificare che **Modalità A** (alimentatore esterno 5 V) e **Modalità B** (USB-C PC) **non siano mai attive insieme**.
   - Al primo avvio in Modalità B (USB-C PC, ramo 5 V esterno scollegato e speaker scollegato), verificare assenza di surriscaldamenti e leggere `~3,3 V` stabili tra `J1-1` (`3V3`) e `J1-22` (`GND`).
7. **Prova Termica Sotto Carico (in FASE 4, prima del montaggio definitivo in LEGO):**
   - Eseguire 15–30 minuti di conversazione / streaming Wi-Fi + audio continuo in Modalità A (5 V esterni) su breadboard e poi in vano chiuso simulato.
   - Verificare assenza di reset/brownout e controllare la temperatura del package `SGM2212` (deve rimanere stabile senza raggiungere soglie critiche; in caso contrario valutare feritoie aggiuntive o regolatore buck esterno 3,3 V).

---

## Appendice – Elementi da Verificare Fisicamente Prima del Cablaggio Definitivo

Prima di acquistare/cablare in via definitiva, confermare sui componenti fisici reali:
1. **Revisione hardware della DevKitC-1 (`v1.0` vs `v1.1`)** e relativo pin LED RGB (`GPIO 48` vs `GPIO 38`).
2. **Pinout serigrafato effettivo della scheda acquistata** (soprattutto se compatibile di terze parti: verificare posizione `5V`, `3V3`, `RST/EN`, `GND`).
3. **Controller effettivo (`SH1106` vs `SSD1306/SSD1315`) e ordine fisico dei pin** (`GND-VCC-SCL-SDA` vs `VCC-GND-SCL-SDA`) del modulo OLED 1,3".
4. **Indirizzo I2C reale** dell'OLED (`0x3C` o `0x3D`).
5. **Dimensioni fisiche esatte dello speaker 4 Ω / 3 W** (diametro/spessore) per il telaio LEGO in FASE 3.
6. **Caratteristiche reali del breakout USB-C e dell'alimentatore** (portata effettiva ≥ 2 A, caduta di tensione sotto carico).
