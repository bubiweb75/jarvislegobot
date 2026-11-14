# HARDWARE_CHECKLIST — Verifiche all'Arrivo Componenti e Preparazione LEGO (FASE 6)

> **Stato:** Da compilare fisicamente quando i componenti elettronici saranno consegnati.
> **Design meccanico di riferimento:** **Companion Hybrid v2 — Visiera Capsula Arrotondata SNOT** ([jarvis_lego_bot_companion_hybrid_v2_visor.mpd](file:///c:/Users/bcava/Desktop/Progetti/JARVIS%20LEGO%20BOT/03-Mechanical-Design/10-Restyling-LEGO-Companion/jarvis_lego_bot_companion_hybrid_v2_visor.mpd)).

---

## 1. Checklist Elettronica all'Arrivo (Prima di Alimentare)

- [ ] **ESP32-S3-DevKitC-1 N16R8:** verificare serigrafia modulo (`ESP32-S3-WROOM-1-N16R8`), porte `USB` / `UART`, GPIO `4, 5, 6, 7, 15, 16, 41, 42, 47`, `3V3`, `5V`, `GND` e posizione di `RST`/`EN`.
- [ ] **Display OLED 1,3" 128×64 I²C:** verificare ordine reale `VCC/GND/SCL/SDA` e controller effettivo (`SH1106` vs `SSD1306`) al Test 1.
- [ ] **Microfono INMP441:** verificare serigrafie `VDD` (solo 3,3 V), `GND`, `L/R`, `WS`, `SCK`, `SD`.
- [ ] **Amplificatore MAX98357A + Speaker 4 Ω / 3 W:** verificare serigrafie `VIN` (5 V), `GND`, `SD`, `GAIN`, `DIN`, `BCLK`, `LRC`, `OUT+`, `OUT-` e polarità `JST-PH2.0`.
- [ ] **Controllo multimetro:** assenza di cortocircuiti tra `5V`/`GND`, `3V3`/`GND` e `OUT+`/`OUT-`/`GND`.

---

## 2. Checklist Verifica Meccanica LEGO (`Companion Hybrid v2 — Visor`)

> **Nota:** L'alloggiamento elettronico interno resta **da confermare** fino alle misure fisiche con calibro.

- [ ] **Dimensioni effettive delle schede (calibro):** ESP32-S3 rispetto alla guida `32316` (`Z = 54 mm`), OLED 1,3" (atteso ~`35,4 × 33,5 mm`) rispetto a finestra `32,0 × 16,0 mm` (`Z = 12,0 mm`) e portello `3036` (`48,0 × 57,6 mm`), ingombro `MAX98357A` e `INMP441`.
- [ ] **Posizione porte USB:** allineamento porta `USB` nativa al passaggio cavo posteriore `L0`.
- [ ] **Dimensioni e profondità speaker:** ingombro magnete sotto la griglia tetto (`L9–L10`).
- [ ] **Accessibilità pulsante:** corsa e fissaggio sul lato sinistro `L3` (`87087` + `98138`).
- [ ] **Passaggio cavi `28 AWG`, ventilazione e facilità di manutenzione** dal portello posteriore `3036`.
