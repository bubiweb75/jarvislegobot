@echo off
cd /d "%~dp0"

if not exist "05-Voice-AI\.venv\Scripts\python.exe" (
    echo [ERRORE] Ambiente virtuale non trovato in 05-Voice-AI\.venv
    pause
    exit /b 1
)

"05-Voice-AI\.venv\Scripts\python.exe" "05-Voice-AI\jarvis_app.py" %*
if errorlevel 1 (
    echo.
    echo [ERRORE] JARVIS Control Center terminato con codice %errorlevel%.
    pause
)
