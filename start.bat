@echo off
title TattooBot Copilot
echo Iniciando Ollama...
start /B ollama serve >nul 2>&1
timeout /t 3 /noqa >nul
echo Iniciando TattooBot...
python main.py
