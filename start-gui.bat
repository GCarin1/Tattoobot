@echo off
title TattooBot Copilot - Desktop
echo Iniciando Ollama...
start /B ollama serve >nul 2>&1
timeout /t 2 /nobreak >nul
echo Iniciando TattooBot Desktop...
pythonw gui_main.py
