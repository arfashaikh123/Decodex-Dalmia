@echo off
setlocal
title Dalmia Load Forecasting GUI

echo ======================================================
echo   ⚡ Dalmia Load Forecasting - GUI Launcher ⚡
echo ======================================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python and add it to PATH.
    pause
    exit /b
)

echo [INFO] Checking dependencies...
pip install -q customtkinter shap lightgbm matplotlib pandas numpy scikit-learn

echo [INFO] Launching GUI...
python gui_load_forecast.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Application crashed. Please check the error message above.
    pause
)

endlocal
