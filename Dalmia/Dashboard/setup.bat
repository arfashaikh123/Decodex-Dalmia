@echo off
REM GRIDSHIELD Dashboard - One-Click Setup Script
REM Run this from PowerShell: .\setup.bat

echo ========================================
echo  GRIDSHIELD Dashboard Setup
echo ========================================
echo.

echo [1/3] Checking Node.js installation...
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js not found!
    echo Please install Node.js from: https://nodejs.org
    echo.
    pause
    exit /b 1
)
echo Node.js detected: 
node --version
echo.

echo [2/3] Installing dependencies...
echo This may take 2-3 minutes...
call npm install
if errorlevel 1 (
    echo ERROR: npm install failed!
    pause
    exit /b 1
)
echo.

echo [3/3] Setup complete!
echo.
echo ========================================
echo  Dashboard is ready to launch!
echo ========================================
echo.
echo To start the dashboard, run:
echo   npm run dev
echo.
echo Or double-click: launch.bat
echo.
pause
