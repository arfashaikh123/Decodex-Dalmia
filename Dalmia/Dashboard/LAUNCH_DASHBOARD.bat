@echo off
title GRIDSHIELD Executive Command Dashboard
color 0A
echo.
echo ========================================
echo   GRIDSHIELD EXECUTIVE COMMAND
echo   Mumbai Load Forecasting Dashboard
echo ========================================
echo.
echo Starting dashboard server...
echo Dashboard will open at: http://localhost:5173
echo.
echo Press Ctrl+C to stop the server
echo.

cd /d "c:\Users\mansu\Downloads\02 – Case GRIDSHIELD\gridshield-dashboard"

:: Check if node_modules exists
if not exist "node_modules\" (
    echo Installing dependencies (first time only)...
    call npm install
    echo.
)

:: Start Vite dev server
call npm run dev

pause
