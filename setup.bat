@echo off
echo ============================================
echo    Forex Trading Bot - Auto Setup Script
echo ============================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from https://python.org/downloads
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo [INFO] Python found - checking version...
python -c "import sys; print(f'Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')"

:: Check if pip is available
pip --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] pip is not available
    echo Installing pip...
    python -m ensurepip --upgrade
)

:: Create virtual environment if it doesn't exist
if not exist "venv" (
    echo [INFO] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
)

:: Activate virtual environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)

:: Upgrade pip in virtual environment
echo [INFO] Upgrading pip...
python -m pip install --upgrade pip

:: Install required packages
echo [INFO] Installing required packages...
pip install flask flask-sqlalchemy flask-socketio
if errorlevel 1 (
    echo [ERROR] Failed to install Flask packages
    pause
    exit /b 1
)

pip install gunicorn eventlet
if errorlevel 1 (
    echo [WARNING] Gunicorn installation failed (Windows compatibility issue)
    echo Using alternative server setup...
)

pip install werkzeug requests pandas numpy
if errorlevel 1 (
    echo [ERROR] Failed to install core packages
    pause
    exit /b 1
)

:: Try to install MetaTrader5 package (optional)
echo [INFO] Installing MetaTrader5 package (optional)...
pip install MetaTrader5
if errorlevel 1 (
    echo [WARNING] MetaTrader5 package installation failed
    echo This is normal if MT5 terminal is not installed
    echo The bot will run in demo mode
)

:: Install additional packages for email notifications
echo [INFO] Installing notification packages...
pip install email-validator
if errorlevel 1 (
    echo [WARNING] Email validator installation failed
)

:: Create default configuration files if they don't exist
echo [INFO] Creating default configuration files...

if not exist "config.json" (
    echo [INFO] Creating default config.json...
    echo { > config.json
    echo   "accounts": [ >> config.json
    echo     { >> config.json
    echo       "name": "Demo Account", >> config.json
    echo       "login": 12345678, >> config.json
    echo       "server": "Exness-Demo", >> config.json
    echo       "password": "your_password_here", >> config.json
    echo       "enabled": false >> config.json
    echo     } >> config.json
    echo   ], >> config.json
    echo   "global_settings": { >> config.json
    echo     "sleep_seconds": 300, >> config.json
    echo     "max_daily_trades": 10, >> config.json
    echo     "risk_percentage": 1.0, >> config.json
    echo     "email_notifications": false, >> config.json
    echo     "smtp_server": "smtp.gmail.com", >> config.json
    echo     "smtp_port": 587, >> config.json
    echo     "email_user": "your_email@gmail.com", >> config.json
    echo     "email_password": "your_app_password" >> config.json
    echo   } >> config.json
    echo } >> config.json
)

if not exist "control.json" (
    echo [INFO] Creating default control.json...
    echo { > control.json
    echo   "status": "running", >> control.json
    echo   "last_updated": "2025-01-01T00:00:00Z" >> control.json
    echo } >> control.json
)

:: Set environment variables for the session
echo [INFO] Setting environment variables...
set SESSION_SECRET=forex-trading-bot-secret-key-2025
set DATABASE_URL=sqlite:///forex_bot.db

:: Create run script for Windows
echo [INFO] Creating Windows run script...
echo @echo off > run.bat
echo call venv\Scripts\activate.bat >> run.bat
echo set SESSION_SECRET=forex-trading-bot-secret-key-2025 >> run.bat
echo set DATABASE_URL=sqlite:///forex_bot.db >> run.bat
echo echo Starting Forex Trading Bot... >> run.bat
echo echo Dashboard will be available at: http://localhost:5000 >> run.bat
echo echo. >> run.bat
echo echo [INFO] Using eventlet server for better WebSocket support... >> run.bat
echo python start_with_eventlet.py >> run.bat
echo pause >> run.bat

:: Make run script executable and create desktop shortcut
echo [INFO] Creating desktop shortcut...
if exist "%USERPROFILE%\Desktop" (
    echo @echo off > "%USERPROFILE%\Desktop\Forex Trading Bot.bat"
    echo cd /d "%CD%" >> "%USERPROFILE%\Desktop\Forex Trading Bot.bat"
    echo call run.bat >> "%USERPROFILE%\Desktop\Forex Trading Bot.bat"
)

:: Test database connection
echo [INFO] Testing database setup...
python -c "from app import app, db; app.app_context().push(); db.create_all(); print('Database setup successful')"
if errorlevel 1 (
    echo [ERROR] Database setup failed
    pause
    exit /b 1
)

:: Check if MetaTrader 5 terminal is installed
echo [INFO] Checking for MetaTrader 5 installation...
if exist "C:\Program Files\MetaTrader 5\terminal64.exe" (
    echo [INFO] MetaTrader 5 found at C:\Program Files\MetaTrader 5\
) else if exist "C:\Program Files (x86)\MetaTrader 5\terminal64.exe" (
    echo [INFO] MetaTrader 5 found at C:\Program Files (x86)\MetaTrader 5\
) else (
    echo [WARNING] MetaTrader 5 not found in standard locations
    echo The bot will run in demo mode without real trading
    echo To enable real trading, install MT5 from your broker
)

:: Final setup verification
echo.
echo ============================================
echo              Setup Complete!
echo ============================================
echo.
echo Next steps:
echo 1. Configure your MT5 account details in config.json
echo 2. Run the bot using: run.bat
echo 3. Access the dashboard at: http://localhost:5000
echo.
echo Files created:
echo - config.json     (trading configuration)
echo - control.json    (bot control settings)
echo - run.bat         (start the bot)
echo - Desktop shortcut (if applicable)
echo.
echo [INFO] Setup completed successfully!

:: Ask user if they want to start the bot now
echo.
set /p start_now="Would you like to start the bot now? (y/n): "
if /i "%start_now%"=="y" (
    echo Starting the bot...
    call run.bat
) else (
    echo You can start the bot anytime by running: run.bat
    pause
)