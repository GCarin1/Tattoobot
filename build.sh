#!/usr/bin/env bash
# Build do TattooBot Desktop (Linux/macOS).
# O executavel resultante nao funciona no Windows - para distribuir pra PC,
# rode o build.bat em uma maquina Windows.

set -e

echo
echo "============================================================"
echo "  TATTOOBOT - BUILD DO EXECUTAVEL"
echo "============================================================"
echo

echo "[1/3] Instalando dependencias..."
python -m pip install --upgrade pip >/dev/null
python -m pip install -r requirements-build.txt

echo
echo "[2/3] Limpando builds anteriores..."
rm -rf build dist

echo
echo "[3/3] Empacotando com PyInstaller..."
python -m PyInstaller tattoobot.spec --clean --noconfirm

echo
echo "============================================================"
echo "  BUILD CONCLUIDO!"
echo "============================================================"
echo
echo "Executavel gerado em:  dist/TattooBot/TattooBot"
echo
