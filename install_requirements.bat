@echo off
echo Installing Python packages for Forex Trading Bot...
echo.

:: Activate virtual environment if it exists
if exist "venv" (
    call venv\Scripts\activate.bat
)

:: Install core Flask packages
pip install Flask==3.0.0
pip install Flask-SQLAlchemy==3.1.1
pip install Flask-SocketIO==5.3.6
pip install Werkzeug==3.0.1

:: Install async support
pip install eventlet==0.33.3

:: Install web server
pip install gunicorn==21.2.0

:: Install data processing
pip install pandas==2.1.4
pip install numpy==1.26.2
pip install requests==2.31.0

:: Install database support
pip install SQLAlchemy==2.0.23
pip install psycopg2-binary==2.9.9

:: Install utilities
pip install email-validator==2.1.0
pip install python-socketio==5.10.0
pip install python-engineio==4.7.1

:: Try to install MetaTrader5 (optional)
echo.
echo Installing MetaTrader5 package (optional)...
pip install MetaTrader5==5.0.45
if errorlevel 1 (
    echo [WARNING] MetaTrader5 package installation failed
    echo This is normal if MT5 terminal is not installed
)

echo.
echo Package installation complete!
pause