# JARVIS LEGO BOT — Diagnostica Isolata GPIO1 (Wokwi Browser)

Progetto minimale e isolato per verificare elettricamente l'ingresso `GPIO1` senza usare `.bin` esterni e senza toccare il firmware JARVIS stabile.

## Procedura su Wokwi Browser

1. Apri **https://wokwi.com/projects/new/esp32-s3**.
2. Nella scheda **`sketch.ino`**, sostituisci tutto con il contenuto di [sketch.ino](sketch.ino).
3. Nella scheda **`diagram.json`**, sostituisci tutto con il contenuto di [diagram.json](diagram.json).
4. Premi il pulsante verde **Start Simulation** (icona Play).
5. Osserva il Serial Monitor (`115200 baud`):
   - **Pulsante rilasciato**: deve stampare continuamente `GPIO1=LOW` ogni `100 ms`.
   - **Pulsante premuto** (clic prolungato su `TOUCH GPIO1` o tasto **`T`**): deve stampare `GPIO1=HIGH` finché resta premuto, poi tornare a `GPIO1=LOW` al rilascio.
