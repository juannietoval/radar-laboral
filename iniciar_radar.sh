#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

echo "================================================================"
echo "          RADAR LABORAL MINIMALISTA - LANZADOR LOCAL"
echo "================================================================"

PYTHON_EXE=""
if [ -f ".venv/bin/python" ]; then
    PYTHON_EXE=".venv/bin/python"
elif [ -f "../.venv/bin/python" ]; then
    PYTHON_EXE="../.venv/bin/python"
fi

if [ -z "$PYTHON_EXE" ]; then
    echo "[INFO] Creando entorno virtual local (.venv)..."
    python3 -m venv .venv
    PYTHON_EXE=".venv/bin/python"
    echo "[INFO] Instalando dependencias..."
    $PYTHON_EXE -m pip install --upgrade pip
    $PYTHON_EXE -m pip install -r requirements.txt
fi

echo "[INFO] Iniciando servidor en http://localhost:8080 ..."
if which xdg-open > /dev/null; then
    xdg-open http://localhost:8080 &
elif which open > /dev/null; then
    open http://localhost:8080 &
fi

$PYTHON_EXE server.py
