# Elaborati C & D – Distinta Componenti (BOM) e Stima Costi

**Progetto:** JARVIS LEGO BOT – FASE 2  
**Nota:** Nessun componente va acquistato in questa fase fino all'approvazione finale del piano.

---

## Elaborato C – Distinta Componenti (BOM)

### C.1 Componenti Elettronici Principali

| ID | Componente | Modello Esatto | Caratteristiche Chiave | Qtà | Dimensioni Indicative | Alternative Compatibili |
|---|---|---|---|---|---|---|
| **U1** | Scheda MCU | **Espressif ESP32-S3-DevKitC-1 N16R8** (o compatibile pin-to-pin N16R8) | 16 MB Flash, 8 MB Octal PSRAM (OPI), Wi-Fi/BLE, doppia USB-C, header saldati | 1 | ~63 × 25,4 × 13 mm | Devboard ESP32-S3-WROOM-1 **N16R8** (verificare sempre serigrafia pin `J1`/`J3` e revisione) |
| **DSP1** | Display OLED | **Modulo OLED 1,3" 128×64 I2C SH1106** (colore bianco o azzurro/ciano) | Controller **SH1106**, interfaccia I2C 4 pin (`0x3C` tipico), alimentazione 3,3 V | 1 | ~35,5 × 33,5 × 4 mm (area attiva ~29,4 × 14,7 mm) | OLED 1,3" 128×64 I2C con controller **SSD1306** o **SSD1315** (4 pin, verifica indirizzo I2C) |
| **MIC1** | Microfono Digitale | **Modulo Breakout INMP441** | MEMS I2S omnidirezionale, SNR 61 dBA, **solo 3,3 V** | 1 | Ø ~14 mm (tondo) o ~14 × 14 mm | Modulo I2S equivalente a 3,3 V (es. ICS-43434) |
| **AMP1** | Amplificatore Audio | **Modulo Breakout MAX98357A** | Classe D I2S mono, fino a 3,2 W su 4 Ω a 5 V, no MCLK | 1 | ~19 × 18 × 3 mm | Modulo MAX98357A con morsettiera a vite (~20 × 20 mm) |
| **SPK1** | Altoparlante | **Mini Speaker 4 Ω / 3 W** | Impedenza 4 Ω, potenza nominale 3 W | 1 | **Ø 36 mm o 40 mm**, spessore ~15–20 mm | Speaker rettangolare/ovale 4 Ω / 3 W (es. 40 × 28 mm) da confermare in FASE 3 |
| **SW1** | Pulsante Attivazione | **Pulsante tattile / da pannello momentaneo NO** | Normalmente Aperto (NO), 2 pin, senza blocco | 1 | 6 × 6 mm (tattile) oppure Ø 12 mm (da pannello) | Microswitch meccanico adatto a incastro LEGO |
| **PWR1** | Ingresso Alimentazione | **Breakout USB-C 5 V con resistenze CC 5,1 kΩ, portata ≥ 2 A** | Solo alimentazione `VBUS` + `GND`. Le CC 5,1 kΩ identificano il dispositivo come *Sink* USB-C a 5 V (non garantiscono 3 A da sole: verificare portata PCB e alimentatore) | 1 | ~15 × 12 × 4 mm | Adattatore USB-C femmina a morsetti con CC 5,1 kΩ e portata ≥ 2 A |
| **PSU1** | Alimentatore | **Alimentatore USB 5 V / ≥ 2 A** (es. 5 V 2,4 A o 3 A) + **cavo USB-C** | Uscita stabile 5 V DC reale ≥ 2 A, cavo con conduttori potenza adeguati (≤ 22 AWG) | 1 | Esterno | Alimentatore certificato 5 V ≥ 2 A (es. ufficiale Raspberry/smartphone di qualità) |

### C.2 Componenti Passivi, Prototipazione e Cablaggi

| ID | Componente | Specifica | Qtà | Note |
|---|---|---|---|---|
| **C1** | Condensatore elettrolitico | **470 µF / 16 V** (o 10 V, low-ESR) | 1–2 | Da collegare tra `5V` e `GND` vicino a `AMP1` |
| **C2** | Condensatore ceramico | **100 nF (0,1 µF) / ≥ 16 V** | 2 | Filtro alta frequenza in parallelo a `C1` |
| **PROTO1** | Breadboard | **Breadboard 830 punti** (o 2× 400 punti affiancate) | 1 | La DevKitC-1 (larghezza ~25,4 mm) lascia 1 sola fila libera per lato su breadboard standard; 2 breadboard affiancate offrono più spazio |
| **WIRE1** | Cavetti prototipo | Kit cavetti **DuPont M-M e M-F** (20 cm / 10 cm) | 1 kit | Per collaudo su breadboard |
| **WIRE2** | Cavi definitivi (per FASE 3/4) | Cavo multifilare silicone **22 AWG** (rosso/nero, alimentazione/speaker) + **26 AWG** (segnali) | ~2 m cad. | Per cablaggio pulito dentro la struttura LEGO |
| **CONN1** | Connettori / Guaina | Connettori **JST-XH 2.54 mm** (o pin header + guaina termorestringente) | 1 kit | Per rendere i moduli smontabili nel corpo LEGO |

---

## Elaborato D – Stima del Costo Complessivo

I prezzi sono stime indicative di mercato al dettaglio (al netto di eventuali spedizioni o componenti già posseduti).

### D.1 Elettronica Principale
| Voce | Costo stimato (EUR) |
|---|---|
| ESP32-S3-DevKitC-1 N16R8 | 7 € – 12 € |
| Display OLED 1,3" 128×64 I2C (SH1106) | 4 € – 7 € |
| Microfono INMP441 I2S | 2 € – 4 € |
| Amplificatore MAX98357A I2S | 3 € – 5 € |
| Altoparlante 4 Ω / 3 W (Ø 36–40 mm) | 2 € – 5 € |
| Pulsante momentaneo + Breakout USB-C 5 V (≥ 2 A) | 2 € – 4 € |
| **Subtotale Elettronica** | **20 € – 37 €** |

### D.2 Cablaggi, Passivi e Prototipazione
| Voce | Costo stimato (EUR) |
|---|---|
| Condensatori (470 µF + 100 nF) | 1 € – 2 € |
| Breadboard 830 punti + kit cavetti DuPont | 5 € – 9 € |
| Cavo silicone 22/26 AWG + connettori/guaina termorestringente | 5 € – 10 € |
| Alimentatore USB 5 V ≥ 2 A + cavo USB-C (se non già disponibile) | 8 € – 14 € |
| **Subtotale Cablaggi & Alimentazione** | **19 € – 35 €** |

### D.3 Materiali LEGO Eventualmente Mancanti
*(La distinta esatta dei mattoncini verrà prodotta in **FASE 3**).*

| Voce | Costo stimato (EUR) |
|---|---|
| Lotto integrativo mattoncini LEGO System (nero, dark bluish gray, azzurro) | 15 € – 30 € |
| Lotto integrativo LEGO Technic (beam, pin, frame interni) | 10 € – 20 € |
| **Subtotale LEGO (se acquistato ex-novo parzialmente)** | **25 € – 50 €** |

### Riepilogo Totale Stimato
- **Solo elettronica + prototipazione (senza alimentatore se già posseduto):** **~31 € – 58 €**
- **Totale completo (elettronica + cablaggi + alimentatore + integrazione LEGO):** **~64 € – 122 €**
