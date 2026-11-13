# README – Audit di Costruibilità Reale LEGO (JARVIS LEGO BOT)

**Data audit e riconciliazione:** 13 novembre 2026  
**Modello LDraw completo (`187` pezzi):** [jarvis_lego_bot.mpd](jarvis_lego_bot.mpd) *(importabile in BrickLink Studio 2.0 / LDCad / LDView)*

## Struttura della cartella
1. [01_Audit_Pezzi_Reali_e_Codici.md](01_Audit_Pezzi_Reali_e_Codici.md) – Verifica codici e Element ID su `csv/` e separazione LEGO / elettronica / adattatori non LEGO.
2. [02_Verifica_Geometrica_e_Incastri.md](02_Verifica_Geometrica_e_Incastri.md) – Analisi geometrica dei 4 moduli, limiti dichiarati dell'ambiente e check AABB 3D (`0` collisioni).
3. [03_Distinta_LEGO_Definitiva.md](03_Distinta_LEGO_Definitiva.md) – Distinta definitiva estratta direttamente da `jarvis_lego_bot.mpd` (**`187` pezzi**: `136 A + 19 B1 + 32 B2`).
4. [04_Istruzioni_Montaggio.md](04_Istruzioni_Montaggio.md) – Sequenza costruttiva per sottoassemblaggi riproducibile dal modello `.mpd`.
5. [05_Verifica_Compatibilita_Elettronica.md](05_Verifica_Compatibilita_Elettronica.md) – Confronto 3D elettronica/cavi e specifica costruttiva degli adattatori non LEGO N20.
6. [06_Problemi_Rilevati_e_Correzioni.md](06_Problemi_Rilevati_e_Correzioni.md) – Problemi risolti, condizioni aperte e verdetto finale.
7. [07_Riconciliazione_MPD_BOM.md](07_Riconciliazione_MPD_BOM.md) – Riconciliazione dettagliata precedente (`173/171/112`) vs corretta (`187/187/187`) e 3 controlli indipendenti.
