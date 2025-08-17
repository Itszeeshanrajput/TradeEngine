# Forex Trading Bot - Troubleshooting Guide

## Common Issues and Solutions

### 1. WebSocket Connection Errors

**Symptoms:**
- "WebSocket disconnected: transport error"
- "Max reconnection attempts reached"
- Dashboard shows connection issues

**Solutions:**
1. **Use the Python development server instead of gunicorn:**
   ```bat
   python start_with_eventlet.py
   ```

2. **Install eventlet if missing:**
   ```bat
   pip install eventlet
   ```

3. **Check firewall settings:**
   - Ensure port 5000 is not blocked
   - Add exception for Python in Windows Firewall

### 2. MetaTrader 5 Issues

**Symptoms:**
- "MetaTrader5 import could not be resolved"
- Trading not working

**Solutions:**
1. **For demo mode (no real trading):**
   - The bot will work without MT5 installed
   - All trading features will use mock data

2. **For real trading:**
   - Download and install MetaTrader 5 from your broker
   - Install the MT5 Python package:
     ```bat
     pip install MetaTrader5
     ```

### 3. Database Issues

**Symptoms:**
- "Database setup failed"
- SQLite errors

**Solutions:**
1. **Delete existing database:**
   ```bat
   del forex_bot.db
   del instance\forex_bot.db
   ```

2. **Recreate database:**
   ```bat
   python -c "from app import app, db; app.app_context().push(); db.create_all()"
   ```

### 4. Python Environment Issues

**Symptoms:**
- Import errors
- Package not found errors

**Solutions:**
1. **Use virtual environment:**
   ```bat
   python -m venv venv
   venv\Scripts\activate.bat
   pip install -r requirements.txt
   ```

2. **Update Python (minimum 3.8 required):**
   - Download from https://python.org/downloads
   - Check "Add Python to PATH" during installation

### 5. Port Already in Use

**Symptoms:**
- "Address already in use"
- Cannot bind to port 5000

**Solutions:**
1. **Find and kill process using port 5000:**
   ```bat
   netstat -ano | findstr :5000
   taskkill /PID <process_id> /F
   ```

2. **Use different port:**
   - Edit the startup files to use port 8000 or 3000

### 6. Configuration Issues

**Symptoms:**
- "Configuration file not found"
- Default settings not working

**Solutions:**
1. **Reset configuration files:**
   ```bat
   del config.json control.json
   ```
   Then restart the bot to recreate defaults

2. **Manual configuration creation:**
   - See config.json.example for reference
   - Ensure JSON syntax is valid

## Performance Optimization

### For Better WebSocket Performance:
1. Use `start_with_eventlet.py` instead of gunicorn
2. Ensure stable internet connection
3. Close other resource-intensive applications

### For Trading Performance:
1. Set appropriate sleep intervals in config.json
2. Limit the number of concurrent accounts
3. Monitor system resources

## Emergency Recovery

### If Everything Fails:
1. **Complete reset:**
   ```bat
   rmdir /s venv
   del *.db *.log config.json control.json
   setup.bat
   ```

2. **Start fresh:**
   - Run setup.bat again
   - Use start_windows.bat for Windows
   - Use start_with_eventlet.py for best compatibility

### Getting Help:
- Check the console output for specific error messages
- Look at the log files in the application directory
- Ensure all dependencies are properly installed
- Verify MetaTrader 5 terminal is running (for real trading)

## File Descriptions

- `setup.bat` - Complete setup script
- `start_windows.bat` - Windows-optimized startup
- `start_with_eventlet.py` - Eventlet-based server (recommended)
- `run_simple.py` - Simple development server
- `config.json` - Trading configuration
- `control.json` - Bot control settings
- `gunicorn.conf.py` - Production server configuration