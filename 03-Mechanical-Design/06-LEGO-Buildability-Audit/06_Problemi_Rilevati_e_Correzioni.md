# 06 – Problemi Rilevati, Correzioni e Valutazione Finale

---

## 1. Problemi Rilevati e Correzioni Applicate

1. **Incongruenza MPD ↔ Distinta (risolta in [07_Riconciliazione_MPD_BOM.md](07_Riconciliazione_MPD_BOM.md)):**
   - Il precedente `.mpd` conteneva `112` parti contro `173` dichiarate (`171` somma reale), omettendo `32054`, `3937`, `3938`, `87087`, `2412b`, `4519`, `56904`, `32316`, `54200`, `3069b`, `2431`, `14769`, `2780`.
   - Rigenerato [jarvis_lego_bot.mpd](jarvis_lego_bot.mpd) completo con **`187` pezzi** (`136 A + 19 B1 + 32 B2`) e distinta estratta automaticamente con corrispondenza 1:1.
2. **Collisioni geometriche risolte:** setto acustico spostato a `Z=26` (`3035`), sportello convertito a `6×12` SNOT su `87087`, cornice OLED/pulsante spostata su `Y=-0,4..0,0`, interfaccia B2 sostenuta da pilastri `3004 + 3023` (nessuna parte sospesa).
3. **Sostituzioni di catalogo reale:** `50951` → `56904 + 56898`; `6558` → `32054`; `3702` DBG → `3702` Black; `4150` → `14769`.

---

## 2. Valutazione Finale Motivata

> **VERDETTO:** Il progetto **JARVIS LEGO BOT è COSTRUIBILE** a livello di struttura LEGO (`187` pezzi reali verificati su catalogo e allineati 1:1 in [jarvis_lego_bot.mpd](jarvis_lego_bot.mpd) con `0` collisioni AABB), **con le seguenti condizioni esplicite ancora aperte**:
> 1. **Verifica CAD su mesh completa (BrickLink Studio 2.0)** non eseguita in questo ambiente (`DA VERIFICARE FISICAMENTE` / import `.mpd`).
> 2. **Progettazione CAD (STL) e prova fisica** dei `2× giunti albero D 3 mm → 4519` e `2× staffe N20` su B2.
> 3. **Inventario fisico utente** `NON VERIFICATO`.
> 4. **Prove fisiche su prototipo** (stabilità B1, gioco/vibrazioni 4 pin `32054`, scatto sportello `87087`, cablaggi low-profile e ingombro batteria 2S).

*(Nessun acquisto, cablaggio o costruzione è avviato o autorizzato).*
