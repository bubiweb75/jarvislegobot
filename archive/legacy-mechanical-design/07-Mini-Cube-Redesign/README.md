# 07 – Mini Cube Redesign (FASE C — Variante C+B Completata)

**Stato attuale:** **FASE C Passaggio 2 completato** ([`jarvis_lego_bot_mini_cube.mpd`](jarvis_lego_bot_mini_cube.mpd), **`120` pezzi**: `98 A + 22 B1`, `0` collisioni su mesh `.dat` di Studio 2.0). In attesa di **validazione visiva in BrickLink Studio 2.0 su Windows** e conferma misure PCB OLED commerciale.  
**Backup FASE B conservato:** [`jarvis_lego_bot_mini_cube_fase_b_backup.mpd`](jarvis_lego_bot_mini_cube_fase_b_backup.mpd) (`108` pezzi).  
**Riferimento storico conservato:** [`../06-LEGO-Buildability-Audit/jarvis_lego_bot.mpd`](../06-LEGO-Buildability-Audit/jarvis_lego_bot.mpd) (`184` pezzi, versione a torre `80 × 80 × 144 mm` — **non sovrascritto**).

---

## Documenti della cartella

1. [01_Analisi_Fattibilita_Mini_Cubo.md](01_Analisi_Fattibilita_Mini_Cubo.md) — Analisi documenti esistenti, obiettivi dimensionali e fattibilità.
2. [02_Confronto_Layout_Interni.md](02_Confronto_Layout_Interni.md) — Confronto tra Layout A, B e **C (approvato)**.
3. [03_Design_Esterno_e_Dimensioni.md](03_Design_Esterno_e_Dimensioni.md) — Dimensioni `80 × 80 × 96 mm` (`10×10×10`), estetica e funzioni delle 6 facce.
4. [04_OLED_Speaker_Tetto_e_Microfono.md](04_OLED_Speaker_Tetto_e_Microfono.md) — OLED `1,3" SH1106` (parametrico), speaker commerciale **PUI Audio `AS03604AR`** (`Ø 36 × 8,8 mm`, `4 Ω`, `3 W`) e microfono `INMP441`.
5. [05_Interfaccia_Modulare.md](05_Interfaccia_Modulare.md) — Modularità `A ↔ B1 (12×12) / B2`, interfaccia `8×8 stud` e `JST-XH 6-pin`.
6. [06_Verifica_Elettronica_e_Termica.md](06_Verifica_Elettronica_e_Termica.md) — Pinout conservato, alimentazione USB / B2, ventilazione passiva e antenna Wi-Fi.
7. [07_Distinta_LEGO.md](07_Distinta_LEGO.md) — Distinta LEGO (`108` pezzi: `96 A + 12 B1`) estratta 1:1 da `jarvis_lego_bot_mini_cube.mpd`.
8. [08_Verifica_Geometrica.md](08_Verifica_Geometrica.md) — Verifica collisioni `.dat` (`0` hit), margini elettronici parametrici e viste SVG derivate dal modello.
9. [09_Istruzioni_Montaggio.md](09_Istruzioni_Montaggio.md) — Sequenza costruttiva per sottoassemblaggi riproducibile dal modello `.mpd`.
10. [10_Problemi_Aperti_e_Decisioni.md](10_Problemi_Aperti_e_Decisioni.md) — Verifiche ancora aperte (Studio GUI, PCB OLED commerciale, inventario utente, prove fisiche).
11. [jarvis_lego_bot_mini_cube.mpd](jarvis_lego_bot_mini_cube.mpd) — Modello LDraw multi-modulo (`main.ldr`, `modulo_a_mini.ldr`, `modulo_b1_mini.ldr`).
