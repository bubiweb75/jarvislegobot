# 04 – Istruzioni di Montaggio (Sottoassemblaggi Reali dal Modello MPD)

> **Nota su istruzioni illustrate:** In questo ambiente non è installato **BrickLink Studio 2.0**, quindi **non sono state generate istruzioni illustrate PDF**. Il file [jarvis_lego_bot.mpd](jarvis_lego_bot.mpd) è strutturato in sottomodelli (`modulo_a.ldr`, `modulo_b1.ldr`, `modulo_b2.ldr`) pronti per l'importazione in Studio 2.0.

---

## 1. Modulo A (`132` pezzi) — Sottoassemblaggi
1. **Base e Fianchi Interfaccia (`Z=0..3`):** posare `2× 3702` sui fianchi (`X=0, 9`), `1× 6111` sul fronte, `2× 3004` sugli angoli posteriori. *Controllo:* fori `3702` liberi e allineati.
2. **Sottoassemblaggio Griglia Speaker (`16` pezzi):** unire `3× 3795` (`Plate 2×6`) formando un `6×6` (`48×48 mm`), rivestire con `9× 2412b` (`Grille Tile`). Fissare `4× 87087` ai 4 angoli interni dell'apertura speaker.
3. **Pareti + Setto + Supporti:**
   - Alternare `3008` (`14` Black, `12` DBG) sui fianchi.
   - Sul fronte montare pilastri `3004` ai lati della griglia e dell'OLED; posare `6111` con `1× 14769` (pulsante); montare **`1× 3035` (`Plate 4×8`)** come setto acustico; montare **`2× 3937 + 2× 3938`** (`4 LDU` di passo) dietro la finestra OLED con cornice **`2× 3069b` + `2× 54200`** (`Medium Azure`); centrare **`1× 3700`** tra `2× 3010` per il microfono.
   - Inserire verticalmente `2× 32316` (`Beam 1×5`) per la slitta `ESP32-S3`.
4. **Sottoassemblaggio Sportello Posteriore (`10` pezzi) + Calotta:**
   - Unire `1× 3036` (`6×8` orientata in verticale) + `1× 3031` (`4×4`) + `2× 3022` (`2×2`), rifinire con `1× 2431` + `1× 3069b`. Agganciare ai `4× 87087` posteriori.
   - Chiudere il tetto con `8× 3040b` perimetrali + `1× 3035` (`4×8` Black) + `2× 3034` (`2×8` Black) + `2× 2412b`.
   - *Controllo manutenzione:* sfilare e reinserire lo sportello senza attrezzi e verificare lo scorrimento della slitta `ESP32-S3`.

## 2. Modulo B1 (`19` pezzi)
1. Unire la piastra `12 × 11` (`2× 3035`, `2× 3031`, `1× 3034`, `1× 3020`, `1× 3460`, `1× 3710`).
2. Posare la cornice perimetrale (`1× 3895`, `2× 2730`) e l'anello interfaccia `8×8` (`2× 3702`, `2× 3009`).

## 3. Modulo B2 (`33` pezzi)
1. Unire `2× 32278` (`1×15` lungo Z) alle traverse `2× 3702` (`1×8`) tramite `4× 2780`.
2. Posare `4× 3004` + `8× 3023` ai 4 angoli interni e montare sopra l'interfaccia `8×8` (`2× 3702`, `2× 3009`).
3. Montare sotto il posteriore il ponte caster: `1× 3020` (`2×4`) + `1× 3022` (`2×2`) + `1× 2654` (`Boat Stud`).
4. Calzare `2× 56898` su `2× 56904` e infilare sui semiassi `2× 4519` attraverso i longheroni `32278`.

## 4. Assemblaggio Modulare Finale (`A ↔ B1/B2`)
- Calzare il Modulo A sopra l'anello `8×8` di B1 (o B2, previa connessione `JST-XH` a base spenta) e bloccare inserendo dall'esterno **`4× 32054`** fino a battuta. *Controllo:* gioco nullo e sfilamento manuale agevole (`DA VERIFICARE FISICAMENTE`).
