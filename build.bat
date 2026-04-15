@echo off
REM Build do TattooBot Desktop como executavel (.exe) no Windows.
REM Uso: execute este arquivo num prompt com Python 3.11+ instalado.

echo.
echo ============================================================
echo   TATTOOBOT - BUILD DO EXECUTAVEL (Windows)
echo ============================================================
echo.

REM Instala dependencias de build (inclui PyInstaller)
echo [1/3] Instalando dependencias...
python -m pip install --upgrade pip >nul
python -m pip install -r requirements-build.txt
if errorlevel 1 (
    echo Erro instalando dependencias.
    exit /b 1
)

REM Limpa builds anteriores
echo.
echo [2/3] Limpando builds anteriores...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM Roda o PyInstaller com o spec do projeto
echo.
echo [3/3] Empacotando com PyInstaller...
python -m PyInstaller tattoobot.spec --clean --noconfirm
if errorlevel 1 (
    echo Erro durante o empacotamento.
    exit /b 1
)

echo.
echo ============================================================
echo   BUILD CONCLUIDO!
echo ============================================================
echo.
echo Executavel gerado em:  dist\TattooBot\TattooBot.exe
echo Voce pode zipar a pasta dist\TattooBot e distribuir.
echo.
pause
