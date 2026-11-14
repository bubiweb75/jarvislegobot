# JARVIS AI Desk Buddy — FASE 5: Voice & AI Hybrid (Windows 11)

Modulo conversazionale vocale e testuale integrato con il simulatore OLED 128×64 di JARVIS.

## Architettura (`05-Voice-AI/`)

- `voice_controller.py`: coordinamento non bloccante Push-to-Talk / testo / interruzione.
- `audio_input.py`: acquisizione microfono Push-to-Talk via Windows WinMM (`winmm.dll`, zero registrazione continua).
- `stt_providers.py`: interfaccia STT sostituibile (`FasterWhisperSTTProvider` opzionale, `WindowsSpeechSTTProvider`, `MockSTTProvider`).
- `ai_providers.py`: `DemoAIProvider` (offline), `OllamaProvider` (`http://localhost:11434`), `OpenAIProvider` (richiede API key + conferma esplicita).
- `tts_providers.py`: sintesi vocale locale Windows `System.Speech` (`Microsoft Elsa Desktop`, `it-IT`) con velocità, volume e stop immediato.
- `conversation.py`: cronologia di sessione in memoria (nessun salvataggio su disco di audio o trascrizioni).
- `eye_bridge.py`: bridge thread-safe verso la GUI `tkinter` (`SimulatorQueueTransport`) e trasporto predisposto `SerialEyeTransport` per ESP32-S3 / Raspberry Pi.
- `config.py` + `prompts/jarvis_system_it.txt`: configurazione e personalità separati dal codice.

## Avvio rapido su Windows 11

Doppio clic su `run_jarvis.bat` oppure da PowerShell:

```powershell
cd "c:\Users\bcava\Desktop\Progetti\JARVIS LEGO BOT\05-Voice-AI"
python jarvis_app.py
```

## Modalità Demo (subito operativa senza installazioni)

1. Lascia il provider su `demo`.
2. Scrivi una domanda nel campo **Domanda testuale** e premi **Invia**.
3. Gli occhi passano automaticamente a `THINKING` -> `SPEAKING` (con voce locale Windows `Microsoft Elsa Desktop`) -> `IDLE` (o `HAPPY` sui saluti/ringraziamenti).

## Configurazione Ollama (locale) o OpenAI (online)

- **Ollama**: installa Ollama per Windows e scarica un modello leggero adatto a Ryzen 7 5700U / 16 GB RAM (es. `qwen2.5:3b` o `llama3.2:3b`), poi seleziona `ollama` nella scheda **Impostazioni & Audio**. Se Ollama non è attivo, JARVIS **non** passa automaticamente al cloud.
- **OpenAI**: copia `.env.example` in `.env`, imposta `OPENAI_API_KEY=...`, seleziona `openai` e spunta la conferma esplicita nella GUI.

## Test automatici

```powershell
cd "c:\Users\bcava\Desktop\Progetti\JARVIS LEGO BOT\05-Voice-AI"
python -m unittest discover -s tests -v
```
