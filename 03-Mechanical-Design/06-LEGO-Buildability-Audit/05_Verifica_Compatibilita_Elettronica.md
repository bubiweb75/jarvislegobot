# 05 – Verifica Compatibilità Elettronica e Adattatori Non LEGO

> **Principio:** Dimensioni compatte invariate; netta separazione tra **parti LEGO originali**, **componenti elettronici** e **adattatori meccanici non LEGO** (senza simulare supporti inesistenti nel `.mpd`).

---

## 1. Modulo A – Vano interno `64 × 64 × 128 mm`

| Componente | Dimensioni reali + connettori | Vano assegnato (`mm`) | Verifica |
| :--- | :--- | :--- | :--- |
| **`ESP32-S3-DevKitC-1 N16R8`** | `63,0 × 25,4 × 13,0 mm` + `~9 mm` DuPont 90° | `X=27,3..52,7`, `Y=50..70`, `Z=14..77` | `14–20 mm` gap verso speaker; `6,2 mm` sotto setto `Z=83,2`; antenna in `Y=50..72` |
| **Accesso `USB-C`** | Spina 90° `~14 mm` o estrazione slitta `32316` | `Z=0..14` + passacavo `16×9,6 mm` post. | Debug via sportello posteriore apribile (`48×96 mm`) |
| **Speaker `4 Ω / 3 W`** | `Ø 40 × 20 mm` + `2 mm` guarnizione | `X=12..52`, `Y=16..36`, `Z=12..52` | Dietro griglia SNOT `2412b`; decentrato per lasciare spazio a `MAX98357A` |
| **`MAX98357A`** | `19 × 18 × 3 mm` + morsetti | `X=54..70`, `Y=16..34`, `Z=12..31` | Affiancato allo speaker |
| **OLED `1,3" SH1106`** | `35,5 × 33,5 × 4,5 mm` + header | `X=22..57,5`, `Y=18..31,5`, `Z=88..121,5` | Inclinato `~15°` su `3937+3938` sopra setto `3035` |
| **`INMP441`** | `Ø 14 × 3 mm` + anello gommapiuma | `X=33..47`, `Y=10..16,5`, `Z=122..134` | Centrato sul foro `3700` |

---

## 2. Modulo B2 – Elettronica, Batteria e Adattatori Meccanici N20 (Non LEGO)

- **Batteria `2S1P` (`≤ 80 × 50 × 20 mm`), `ESP32-C3`, `TB6612FNG`, `INA3221`, `Buck 6V/5V`, `VL53L0X`:** posizionati tra i longheroni `32278` (`64 mm` luce interna) e davanti all'interfaccia (`VL53L0X` a `Y=10..22 mm`). Ingombro reale finale subordinato al modello commerciale di batteria scelto (`DA VERIFICARE FISICAMENTE`).

### Specifica dettagliata elementi non LEGO da realizzare (B2)
Poiché i micro-motoriduttori **N20** (`24 × 12 × 10 mm`, albero D `Ø 3,0 mm` lungo `9–10 mm`) non sono nativamente compatibili con lo standard LEGO Technic (`Ø 4,8 mm`), restano da progettare e realizzare:

1. **2× Giunti meccanici `Albero D 3 mm → Asse LEGO Technic 4519`:**
   - **Geometria:** boccola cilindrica (`Ø_est ≈ 7,5 mm`, lunghezza `14–16 mm`): lato motore con foro a D `Ø 3,05 mm` (profondità `8 mm`) + grano filettato `M2`/`M2,5` radiale; lato ruota con cava a croce Technic (`4,8 mm`, profondità `6–8 mm`) per innesto dell'asse **`4519` (`3L`)**.
   - **Materiale e fabbricazione:** stampa 3D in **PETG/ABS/Nylon** (infill `100%`, ugello `0,2–0,4 mm` + eventuale grano `M2`) oppure **alluminio tornito/fresato** (o giunto commerciale `3 mm → 4 mm` adattato).
   - **Stato:** **DA PROGETTARE (CAD STL)** e **`DA VERIFICARE FISICAMENTE`** (tolleranza accoppiamento croce Technic).
2. **2× Staffe / culle motore N20 → Longheroni `32278`:**
   - **Geometria:** culla a U interna `12,2 × 10,2 mm` (lunghezza `18 mm`) con due alette dotate di fori `Ø 4,9 mm` a passo **`8,0 mm`** per fissaggio diretto sui fori dei longheroni **`32278`** tramite pin `2780` o viti/dadi M3.
   - **Materiale e fabbricazione:** stampa 3D **PETG/ABS** (spessore parete `≥ 2,0 mm`) oppure staffa metallica piegata + fascette di bloccaggio assiale.
   - **Stato:** **DA PROGETTARE (CAD STL)** e **`DA VERIFICARE FISICAMENTE`** (allineamento coassiale motore-foro `32278` senza attriti).
