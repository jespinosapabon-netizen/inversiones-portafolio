@echo off
title Lanzador - SST Wealth Management System
echo ==========================================================
echo   Iniciando SST - Wealth Management System...
echo   Esta ventana debe permanecer abierta mientras uses la app.
echo ==========================================================
echo.
cd /d "C:\Users\jespi\.gemini\antigravity\scratch\investments_tracker"
python -m streamlit run app.py
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] No se pudo iniciar Streamlit a traves de Python.
    echo intentando instalar dependencias por si faltan...
    python -m pip install -r requirements.txt
    echo reintentando iniciar...
    python -m streamlit run app.py
)
pause
