# Disegno Dimensionale e Verifica Meccanica 3D — JARVIS Carrier Board V1

- **Disegni vettoriali e 3D esportati nella stessa cartella:**
  - [JARVIS_Carrier_V1_LAYOUT.pdf](JARVIS_CARRIER_BOARD_V1_FINAL/JARVIS_Carrier_V1_LAYOUT.pdf)
  - [JARVIS_Carrier_V1_LAYOUT.svg](JARVIS_CARRIER_BOARD_V1_FINAL/JARVIS_Carrier_V1_LAYOUT.svg)
  - [GERBERS/JARVIS_Carrier_V1-drl_map.pdf](JARVIS_CARRIER_BOARD_V1_FINAL/GERBERS/JARVIS_Carrier_V1-drl_map.pdf)
  - [JARVIS_Carrier_V1_3D_TOP.png](JARVIS_CARRIER_BOARD_V1_FINAL/JARVIS_Carrier_V1_3D_TOP.png)
  - [JARVIS_Carrier_V1_3D_BOT.png](JARVIS_CARRIER_BOARD_V1_FINAL/JARVIS_Carrier_V1_3D_BOT.png)

---

## 1. Verifica Ingombri Tridimensionali nel Vano LEGO (`64,0 × 64,0 × 86,4 mm`)

La revisione precedente (`63,0 × 74,0 mm`) lasciava solo `0,5 mm` per lato. La scheda finale è stata compattata a **`60,0 × 74,0 mm`** (senza ridurre alcuna distanza elettrica minima né modificare la mappatura GPIO):

| Asse / Elemento | Ingombro Reale Assemblato | Vano LEGO Dichiarato | Margine Residuo e Note di Montaggio |
| :--- | :---: | :---: | :--- |
| **Larghezza (`X`) PCB** | **`60,0 mm`** | `64,0 mm` (`8×8 stud`) | **`4,0 mm` totali (`2,0 mm` per lato)**. Inserimento dall'alto rimuovendo il coperchio tetto `L9–L10` (il portello posteriore `3036` è largo `48,0 mm`, quindi la PCB entra dall'alto). |
| **Altezza (`Y`) PCB + DevKitC-1** | **`74,0 mm`** (DevKit `Y = 2,0..70,8 mm`) | `86,4 mm` | **`12,4 mm` verticali liberi** sopra/sotto per antenna PCB e connettore USB-C inferiore. |
| **Spessore (`Z`) PCB + Socket + ESP32-S3** | `1,6 mm` (PCB) + `8,5 mm` (socket std) + `4,8 mm` (DevKitC-1) = **`14,9 mm`** | `48,0 mm` dietro OLED (`Z=16..64 mm`) | **`~31 mm` di aria libera** verso l'OLED anteriore (`Z=16 mm`). |
| **Spessore (`Z`) JST-XH + Cavi + `C1`** | JST-XH `7,0 mm` + spina XHP + piega cavi `~7–8 mm` = **`~15 mm`**; `C1` (`470 µF`): **`~12 mm`** | `48,0 mm` dietro OLED | I connettori JST-XH sporgono sul lato componenti (`F.Cu`) rivolti verso lo spazio aperto interno tra PCB e OLED. |
| **Porta USB-C e Cavo** | Bordo inferiore DevKitC-1 a `Y = 70,8 mm` (centro `X = 29,5 mm`) | Varco `L0/L1` (`48,0 × 9,6 mm`) | Usare **cavo USB-C a 90°** (ingombro `~12–14 mm`) oppure sfilare leggermente verso l'alto per il collegamento al PC, uscendo dal varco inferiore posteriore `L0/L1`. |
| **Fori di Fissaggio (`H1`, `H2`)** | `2× Ø 3,2 mm` (M3) a `X = 29,50 mm`, `Y = 20,00` e `52,00 mm` | Passo LEGO Technic `32,00 mm` (`4 × 8,00 mm`) | Posizionati al centro tra `J1` e `J3`. Montare i distanziali M3 in nylon **prima** di inserire l'ESP32-S3 nei socket `J1`/`J3`. |
| **Antenna Wi-Fi Keep-Out** | `X = 20,0..39,0 mm`, `Y = 0,6..8,8 mm` | Zona superiore libera sotto griglia | Esclusione totale di rame, piste e vie su `F.Cu` e `B.Cu`. |

---

## 2. Coordinate dei Componenti (`mm`, origine angolo alto-sinistra `(0, 0)`)

| Rif. | Descrizione | X (mm) | Y (mm) | Orientamento | Note |
| :---: | :--- | :---: | :---: | :---: | :--- |
| **`H1` / `H2`** | Fori M3 (`Ø 3,2 mm`) | `29,50` | `20,00` / `52,00` | `0°` | Interasse `32,00 mm` (`4 × 8 mm` LEGO). |
| **`J1` / `J3`** | Socket 1×22 ESP32-S3 | `18,07` / `40,93` | `10,00` | `0°` | Interasse esatto `22,86 mm` (`0,900 in`). |
| **`J4`** | OLED SH1106 (4 pin JST-XH) | `4,80` | `10,00` | `270°` | Pin 1=`GND`, 2=`+3V3`, 3=`SCL`, 4=`SDA`. |
| **`J5`** | INMP441 Mic (6 pin JST-XH) | `4,80` | `25,00` | `270°` | Ala sinistra. |
| **`J6`** | MAX98357A Amp (7 pin JST-XH) | `4,80` | `44,00` | `270°` | Ala sinistra. |
| **`C1`** | `470 µF / 16 V` (`Ø 8 mm`) | `6,50` | `67,00` | `0°` | Vicino a `J6` (`+5V` / `GND`). |
| **`J8`** | Pulsante PTT (2 pin JST-XH) | `47,50` | `10,00` | `270°` | Colonna destra interna. |
| **`J9`** | Touch TTP223B (3 pin JST-XH) | `47,50` | `19,50` | `270°` | Colonna destra interna. |
| **`J13`** | Base Mobile B2 (6 pin JST-XH) | `47,50` | `32,00` | `270°` | `JP1` aperto (`+5V` isolato). |
| **`J14`** | AMP BTL IN (2 pin JST-XH) | `47,50` | `51,50` | `270°` | Da `OUT+`/`OUT-` MAX98357A. |
| **`J7`** | Speaker 4 Ω / 3 W (2 pin JST-PH) | `47,50` | `62,00` | `270°` | Uscita BTL isolata da `GND`. |
| **`J10`** | VL53L0X ToF (6 pin JST-XH) | `55,80` | `10,00` | `270°` | Colonna destra esterna. |
| **`J11`** | BH1750 Lux (5 pin JST-XH) | `55,80` | `31,50` | `270°` | Colonna destra esterna. |
| **`J12`** | MPU6050 GY-521 (8 pin JST-XH) | `55,80` | `48,00` | `270°` | Colonna destra esterna. |
| **`JP1`** | Jumper isolamento 5 V B2 | `29,50` | `62,00` | `0°` | Aperto (`DNP`). |
