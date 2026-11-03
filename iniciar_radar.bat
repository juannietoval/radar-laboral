@echo off
setlocal enabledelayedexpansion
title Radar Laboral Minimalista

cd /d "%~dp0"

echo ================================================================
echo           RADAR LABORAL MINIMALISTA - LANZADOR LOCAL
echo ================================================================
echo.

:: 1. Verificar si existe entorno virtual en la carpeta actual o en la superior
set "PYTHON_EXE="
if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=.venv\Scripts\python.exe"
) else if exist "..\.venv\Scripts\python.exe" (
    set "PYTHON_EXE=..\.venv\Scripts\python.exe"
)

:: 2. Si no existe entorno virtual, crearlo automáticamente
if not defined PYTHON_EXE (
    echo [INFO] No se detecto un entorno virtual configurado.
    echo [INFO] Verificando instalacion de Python en el sistema...
    
    python --version >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] No se encontro Python en este equipo.
        echo Por favor instala Python 3.10 o superior desde https://www.python.org/
        echo Asegurate de marcar la casilla "Add python.exe to PATH" durante la instalacion.
        echo.
        pause
        exit /b 1
    )
    
    echo [INFO] Creando entorno virtual local (.venv)...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Fallo al crear el entorno virtual.
        pause
        exit /b 1
    )
    
    set "PYTHON_EXE=.venv\Scripts\python.exe"
    echo [INFO] Instalando dependencias necesarias (esto solo ocurre la primera vez)...
    !PYTHON_EXE! -m pip install --upgrade pip
    !PYTHON_EXE! -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Hubo un problema al instalar las dependencias.
        pause
        exit /b 1
    )
    echo [OK] Entorno virtual preparado con exito.
    echo.
)

:: 3. Iniciar el servidor y abrir el navegador
echo [INFO] Iniciando servidor en http://localhost:8080 ...
start "" http://localhost:8080
!PYTHON_EXE! server.py

if errorlevel 1 (
    echo [ERROR] El servidor se detuvo con errores.
    pause
)
