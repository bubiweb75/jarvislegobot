# README – Audit di Costruibilità Reale LEGO (JARVIS LEGO BOT)

**Data audit e riconciliazione:** 13 novembre 2026  
**Modello LDraw completo (`184` pezzi):** [jarvis_lego_bot.mpd](jarvis_lego_bot.mpd) *(verificato su mesh `.dat` di BrickLink Studio 2.0; importabile in Studio 2.0 / LDCad / LDView)*

## Struttura della cartella
1. [01_Audit_Pezzi_Reali_e_Codici.md](01_Audit_Pezzi_Reali_e_Codici.md) – Verifica codici e Element ID su `csv/` e separazione LEGO / elettronica / adattatori non LEGO.
2. [02_Verifica_Geometrica_e_Incastri.md](02_Verifica_Geometrica_e_Incastri.md) – Analisi geometrica dei 4 moduli e check su mesh `.dat` Studio 2.0 (`0` collisioni).
3. [03_Distinta_LEGO_Definitiva.md](03_Distinta_LEGO_Definitiva.md) – Distinta definitiva estratta direttamente da `jarvis_lego_bot.mpd` (**`184` pezzi**: `132 A + 19 B1 + 33 B2`).
4. [04_Istruzioni_Montaggio.md](04_Istruzioni_Montaggio.md) – Sequenza costruttiva per sottoassemblaggi riproducibile dal modello `.mpd`.
5. [05_Verifica_Compatibilita_Elettronica.md](05_Verifica_Compatibilita_Elettronica.md) – Confronto 3D elettronica/cavi e specifica costruttiva degli adattatori non LEGO N20.
6. [06_Problemi_Rilevati_e_Correzioni.md](06_Problemi_Rilevati_e_Correzioni.md) – Problemi risolti, condizioni aperte e verdetto finale.
7. [07_Riconciliazione_MPD_BOM.md](07_Riconciliazione_MPD_BOM.md) – Riconciliazione dettagliata precedente (`173/171/112`) vs v2 (`184/184/184`) e 3 controlli indipendenti.
8. [08_Correzione_Collisioni_Studio.md](08_Correzione_Collisioni_Studio.md) – Analisi delle cause radice delle collisioni in BrickLink Studio 2.0, correzioni LDraw applicate e verifica sui `.dat` ufficiali.
