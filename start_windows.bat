@echo off
title Forex Trading Bot - Windows Server
echo ============================================
echo       Forex Trading Bot - Windows Server
echo ============================================
echo.

:: Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

:: Set environment variables
set SESSION_SECRET=forex-trading-bot-secret-key-2025
set DATABASE_URL=sqlite:///forex_bot.db

:: Check if eventlet is installed
python -c "import eventlet" 2>nul
if errorlevel 1 (
    echo [ERROR] eventlet is not installed
    echo Installing eventlet...
    pip install eventlet
)

echo Starting Forex Trading Bot...
echo.
echo Dashboard URL: http://localhost:5000
echo Analytics: http://localhost:5000/analytics  
echo Backtest: http://localhost:5000/backtest
echo Settings: http://localhost:5000/settings
echo.
echo Press Ctrl+C to stop the server
echo.

:: Use run_simple.py for better Windows compatibility
python run_simple.py

pause