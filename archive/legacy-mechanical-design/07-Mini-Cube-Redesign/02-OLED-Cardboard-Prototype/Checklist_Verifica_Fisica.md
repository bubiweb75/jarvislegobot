# Checklist di Verifica Fisica — Prototipo OLED in Cartoncino

> **Obiettivo:** Raccogliere riscontri reali sul modulo OLED Binghe 1,3" prima di finalizzare la culla 3D e aggiornare `jarvis_lego_bot_mini_cube.mpd`.
> **Distinzione metodologica:** Questa checklist separa esplicitamente le verifiche valide sul **cartoncino** da quelle che richiederanno la **prova con supporto rigido stampato in 3D**.

---

## 1. Controlli preliminari di stampa (Obbligatori prima delle prove)

- `[ ]` Pagina 1 — Quadrato di controllo misura esattamente **`50,0 × 50,0 mm`** (`±0,3 mm`).
- `[ ]` Pagina 1 — Righello di controllo misura esattamente **`100,0 mm`**.
- `[ ]` Pagina 2 — Quadrato di controllo misura esattamente **`50,0 × 50,0 mm`** (`±0,3 mm`).
- `[ ]` Spessore singolo strato di cartoncino misurato: **`______ mm`** (quindi `4` strati = **`______ mm`**).

---

## 2. Verifiche eseguibili CON IL CARTONCINO

| Area di verifica | Criterio di esito positivo | Esito | Note / Misure rilevate |
|---|---|---:|---|
| **Compatibilità dimensionale PCB** | Il display reale corrisponde a **E1 (`36×34`)**, **E2 (`35,4×33,5`)** o altra misura; entra nella culla **B** senza forzare | `[ ]` | Variante: `E1 / E2 / Altro: ______` |
| **Centraggio del volto** | Con area attiva centrata nella finestra `32×19,2 mm`, né il flex inferiore né i bordi PCB toccano le pareti LEGO | `[ ]` | Offset stimato: `______ mm` |
| **Profondità di incasso** | Con **`____`** strati **C** (`~1,8 mm` o altro), l'aspetto frontale è pulito e il vetro resta protetto | `[ ]` | Strati usati: `____` (`____ mm`) |
| **Visibilità frontale e laterale** | Gli occhi simulati **D1/D2** restano interamente visibili da posizione scrivania fino a ~`±25°–35°` orizzontali | `[ ]` | Angolo limite osservato: `±____°` |
| **Spazio connettori e cablaggio** | I 4 pin superiori escono dallo scasso `14 mm` senza toccare `L7`, `AS03604AR` sul tetto o il percorso verso `ESP32-S3` | `[ ]` | Tipo pin: `Dritti / 90° / Da saldare` |
| **Accessibilità sportello posteriore** | Le linguette della culla e il retro della PCB sono raggiungibili attraverso lo sportello `3036` (`6×8`) | `[ ]` | Note accesso: `______________` |
| **Possibilità di rimozione** | Il gruppo culla + display può essere estratto dal retro senza smontare le pareti laterali o il tetto | `[ ]` | `[ ] OK` / `[ ] Critico` |
| **Compatibilità struttura LEGO** | La tasca `48,0 × 41,6 mm` (`6` stud × `13` plate) e il resto del corpo `80×80×96 mm` restano stabili senza interferire con `4070+3070b` | `[ ]` | `[ ] OK` / `[ ] Note: ________` |

---

## 3. Verifiche che richiedono il SUPPORTO RIGIDO (Stampato in 3D)

Le seguenti verifiche **non possono essere considerate conclusive** con il cartoncino e andranno eseguite sul prototipo rigido definitivo (dopo aver inserito le misure fisiche in `oled_support_parametric.scad`):

1. **Rigidezza meccanica del serraggio senza colla:** Verifica che le flange laterali della cornice 3D (`Z = 8..11 mm`) e le viti M2,5 sulle asole `±2,5 mm` blocchino stabilmente la culla sulle pareti LEGO senza gioco o flessioni nel tempo.
2. **Tolleranza reale di stampa FDM/SLA (`±0,20..0,25 mm`):** Verifica dell'accoppiamento a filo nella tasca LEGO `48,0 × 41,6 mm` e dell'alloggiamento perimetrale della PCB senza incastri forzati.
3. **Zero pressione sul vetro sotto serraggio:** Controllo definitivo che, stringendo le viti della culla rigida, il vetro (`1,4 mm`) resti completamente scarico nello spazio `1,8 + 0,35 mm`.
4. **Centratura ottica a display acceso:** Verifica finale dell'area attiva accesa (`128×64`, dopo aver risolto **`SH1106` vs `SSD1106`** nel firmware) prima del bloccaggio definitivo delle viti asolate.

---

**Prossimo passo:** Esegui la prova con il cartoncino seguendo [Guida_Montaggio_Cartoncino.md](Guida_Montaggio_Cartoncino.md), compila questa checklist insieme alle quote `A..M` e condividi i risultati per finalizzare la culla 3D e aggiornare `jarvis_lego_bot_mini_cube.mpd`.
