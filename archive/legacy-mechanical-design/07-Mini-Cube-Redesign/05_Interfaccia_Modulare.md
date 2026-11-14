# 05 – Modularità Corpo A / Base Fissa B1 / Futura Base Mobile B2

---

## 1. Principio Invariato di Trasferibilità

Il **Corpo A (`10 × 10 stud` = `80 × 80 × 96 mm`)** è progettato fin dall'origine per essere **sganciato dalla base fissa B1 e montato sulla futura base mobile B2 senza smontare o ricablare l'elettronica interna**.

---

## 2. Valutazione dell'Interfaccia Universale `8 × 8 stud`

Con il corpo che mantiene l'impronta esterna **`10 × 10 stud` (`80 × 80 mm`)**, l'interfaccia inferiore **`8 × 8 stud` (`64 × 64 mm`)** con anello di incastro alto `1 brick` (`9,6 mm`) resta **geometricamente valida e meccanicamente ottimale** anche per il Mini Cubo:

- **Vantaggi nel mantenerla:**
  1. **Compatibilità diretta con B1 e B2:** stessa impronta `8×8 stud` già definita nei documenti B2 (`05-Mobile-Electronics/`), senza costringere il corpo A ad aumentare di altezza.
  2. **Altezza contenuta:** l'anello `8×8` di B1/B2 entra **dentro** il primo `brick` (`9,6 mm`) del fondo di A, quindi **non aggiunge altezza** al corpo quando è montato.
  3. **Passaggio cavi integrato:** al centro dell'anello `8×8` resta una luce netta `6×6` / `2×4 stud` per il connettore **`JST-XH 6-pin`** (`+5V_A`, `GND`, `UART_TX_A`, `UART_RX_A`, `I2C_SDA`, `I2C_SCL`).
- **Valutazione dei `4× pin 32054 (3L con stop bush)`:**
  - Nei test del progetto precedente i `4× 32054` (2 per fianco, estratti lateralmente a mano) offrono un bloccaggio sicuro contro ribaltamenti durante il movimento di B2.
  - **Alternativa più comoda per l'uso da scrivania (da approvare per FASE B):** usare `4× 32054` solo quando A è montato su B2 (dove ci sono accelerazioni e vibrazioni) oppure `2× 32054` contrapposti (1 SX + 1 DX) su B1 per uno sgancio ancora più rapido, mantenendo tutti e 4 i fori `3702` predisposti sul corpo A.

---

## 3. Base Fissa B1 (per Mini Cubo)

- **Dimensioni proposte:** **`12 × 12 stud` (`96 × 96 mm`)** oppure **`12 × 11 stud` (`96 × 88 mm`)**, con basamento sottile **`1–2 plate` (`3,2–6,4 mm`)** + anello centrale `8 × 8 × 1 brick` che scompare dentro il corpo A.
- **Altezza esposta di B1 sotto il corpo A:** soli **`3,2 – 6,4 mm`** → altezza totale robot su scrivania = **`99,2 – 102,4 mm`** (perfettamente nell'obiettivo `100–115 mm`).
- **Stabilità:** baricentro molto più basso rispetto alla vecchia torre da `144 mm`; zero elettronica attiva in B1; eventuali piedini in gomma adesivi sottili sotto la piastra base.

---

## 4. Compatibilità Futura con Base Mobile B2

- La futura base mobile **B2** (`~16 × 15 stud`, 2 ruote motrici N20 + caster posteriore, controller `ESP32-C3`, driver `TB6612FNG`, sensori `INA3221`, batteria `2S 18650`, `Buck 6V/5V`, `LM66100`) si aggancia **sotto** lo stesso anello `8×8` tramite il connettore **`JST-XH 6-pin`**.
- **Nota esplicita:** B2 resta un progetto successivo e **non è dichiarata pronta** fino alla progettazione CAD e prova fisica dei `2× giunti D 3 mm → 4519`, delle `2× staffe motore N20`, della distribuzione dei pesi sotto il nuovo Mini Cubo e delle prove di sicurezza elettrica.
- Il Mini Cubo non richiede alcun aumento di altezza per ospitare B2, poiché tutta la logica motori, batteria e regolazione rimane confinata in B2.
