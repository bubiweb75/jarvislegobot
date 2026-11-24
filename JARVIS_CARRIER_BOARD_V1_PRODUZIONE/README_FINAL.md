# JARVIS LEGO BOT — Carrier Board V1 (`JARVIS_CARRIER_BOARD_V1_FINAL`)

- **Stato Finale:** **`PRONTO PER ORDINE`** *(per la scheda Carrier Board PCB V1 da scrivania alimentata via USB-C; completare le verifiche fisiche residue sui cablaggi dei singoli breakout prima di collegare i moduli).*

---

## 1. Modifiche Apportate in Questa Revisione Finale

1. **Correzione Pinout OLED `J4` (Binghe SH1106):**
   - Aggiornato `J4` in schema, PCB, netlist, serigrafia e tabelle all'ordine fisico reale del display: **`Pin 1 = GND`**, **`Pin 2 = +3V3 (VCC)`**, **`Pin 3 = I2C_SCL (GPIO42)`**, **`Pin 4 = I2C_SDA (GPIO41)`**.
2. **Compattazione Meccanica (`63,0 × 74,0 mm` → `60,0 × 74,0 mm`):**
   - Ridotta la larghezza esterna a **`60,0 mm`** per garantire **`2,0 mm` di margine per lato** (`4,0 mm` totali) all'interno del vano LEGO `64,0 × 64,0 × 86,4 mm`, mantenendo invariate tutte le distanze elettriche minime (`clearance >= 0,20 mm` segnali, `>= 0,25 mm` potenza/BTL, `>= 0,50 mm` bordo rame).
3. **Rafforzamento Pista `+5V`:**
   - Larghezza nominale pista `+5V` portata a **`0,60 mm`** verso `C1` (`470 µF`) e `J6-1` (`MAX98357A VIN`).
4. **Abilitazione Esplicita Controlli KiCad Precedentemente Ignorati:**
   - Abilitati in `JARVIS_Carrier_V1.kicad_pro`: `missing_courtyard` (`warning`), `footprint_filters_mismatch` (`warning`), `footprint_type_mismatch` (`error`), `track_not_centered_on_via` (`warning`) e `footprint_filter` (`warning` in ERC).

---

## 2. Verifiche KiCad 10.0.8 Eseguite e Superate

| Verifica | Strumento / Modalità | Esito Reale Misurato |
| :--- | :--- | :--- |
| **ERC completo** | `kicad-cli sch erc` (incluso `footprint_filter`) | ✅ **`0` violazioni** |
| **DRC completo + Parità Schema–PCB** | `kicad-cli pcb drc --schematic-parity` (inclusi `missing_courtyard`, `footprint_filters_mismatch`, `footprint_type_mismatch`, `track_not_centered_on_via`) | ✅ **`0` violazioni**, **`0` non connessi**, **`0` errori di parità** |
| **Corrispondenza 44 pin DevKitC-1 v1.1** | Confronto con documentazione e DXF ufficiale Espressif (`22,86 mm` interasse) | ✅ **`44/44` contatti verificati** |
| **Geometria, Fori e Orientamento** | Analisi 3D + `Edge.Cuts` `60,0 × 74,0 mm` + `H1/H2` M3 (`32,0 mm`) + `JST-XH` `270°` | ✅ **Verificati** |
| **Gerber X2 e Foratura Excellon** | `kicad-cli pcb export gerbers` + `drill` | ✅ **Rigenerati in `GERBERS/`** |

### Controlli Esclusi nel Report KiCad (Default KiCad Non Applicabili)
- **ERC:** `single_global_label` (non usiamo etichette globali su foglio singolo), `four_way_junction` (stile grafico), `simulation_model_issue` (nessuna simulazione SPICE).
- **DRC:** `tuning_profile_track_geometries` (nessuna coppia differenziale ad alta velocità con tuning di lunghezza sul PCB).

---

## 3. Controllo Alimentazione (USB 5 V → ESP32 + MAX98357A) e Sicurezza

- **Percorso 5 V USB:** Sulla `ESP32-S3-DevKitC-1 v1.1`, la VBUS USB attraversa i diodi Schottky onboard `D1`/`D7` (`1N5819HW-7-F`, **`1,0 A` max continui**, caduta `~0,35–0,45 V`) per alimentare il pin `J1-21` (`5V` → `~4,55–4,65 V` sotto carico).
- **Assorbimento stimato:** Media operativa `~500–625 mA` (ESP32-S3 `~220 mA` + OLED/sensori `~45 mA` + MAX98357A `~230–340 mA`). Picco simultaneo teorico Wi-Fi TX + audio 100% 3 W = `~1,15–1,25 A`: il firmware limita il volume (`<= 25%`) e `C1` (`470 µF / 16 V`) + `C2` (`100 nF`) assorbono i transienti locali presso `J6-1`.
- **Rail `+3V3`:** LDO onboard `SGM2212-3.3` (`800 mA` max) alimenta OLED e sensori (`~45 mA` esterni + `ESP32-S3`).
- **Base Mobile B2 (`J13`):** `J13-1` (`B2_5V_ISOLATED`) è **completamente isolato** da `+5V` tramite **`JP1` aperto (`DNP`)**. **Non ponticellare `JP1` né collegare alimentazione B2 insieme alla USB** senza un circuito dedicato di selezione e protezione anti-backfeed.
- **Speaker BTL (`J14` → `J7`):** `SPK_PLUS` e `SPK_MINUS` sono instradati a `0,70 mm` e **completamente isolati da `GND`**.
- **MAX98357A `SD` e `GAIN`:** `J6-3` (`SD`) è collegato a `+3V3` (abilita canale Left, compatibile con duplicazione mono L=R del firmware); `J6-4` (`GAIN`) è `NC` (`9 dB` di guadagno default).

---

## 4. Verifiche Fisiche Ancora Necessarie (Sui Moduli Commerciali)

1. **Resistenza equivalente pull-up I²C0 (`GPIO41/42`):** `R6` e `R7` sulla Carrier Board sono `DNP`. Prima di alimentare tutti i 4 moduli I²C (`OLED`, `VL53L0X`, `BH1750`, `MPU6050`) contemporaneamente, misurare a banco con multimetro la resistenza tra `SDA`/`3V3` e `SCL`/`3V3`: se `< 2,2 kΩ`, dissaldare le resistenze pull-up SMD da 1–2 breakout (`MPU6050`/`BH1750`).
2. **Ordine pin dei cavi JST-XH verso breakout remoti (`J5..J12`):** verificare la serigrafia fisica di ciascun modulo (`INMP441`, `MAX98357A`, `VL53L0X`, `BH1750`, `MPU6050`, `TTP223B`) prima di crimpare i relativi cavetti JST-XH.
3. **Dropout LDO su `MPU6050 GY-521`:** verificare col multimetro che `GY-521` funzioni stabilmente alimentato a `3,3 V` su `J12-1`.
4. **Cavo USB-C a 90° e montaggio dall'alto:** verificare dal vivo l'inserimento della scheda (`60 × 74 mm`) dall'apertura superiore del telaio LEGO e l'uscita del cavo USB-C dal varco posteriore `L0/L1`.
