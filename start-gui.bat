@echo off
title TattooBot Copilot - Desktop

echo Iniciando Ollama...
start /B ollama serve >nul 2>&1
timeout /t 2 /nobreak >nul

echo Iniciando TattooBot Desktop...

REM Usa pythonw (sem console) se disponivel. Se houver erro de startup,
REM gui_main.py grava em data\gui_error.log e mostra um messagebox.
REM Se pythonw nao existir no PATH, caimos pro python normal.
where pythonw >nul 2>&1
if %ERRORLEVEL%==0 (
    pythonw gui_main.py
) else (
    echo [!] pythonw nao encontrado, usando python ^(console visivel^).
    python gui_main.py
    if %ERRORLEVEL% NEQ 0 (
        echo.
        echo [X] TattooBot Desktop encerrou com erro. Veja data\gui_error.log
        pause
    )
)
