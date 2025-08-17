# Forex Trading Bot

A comprehensive automated Forex trading bot with real-time web dashboard, built with Flask and MetaTrader 5 integration.

## Features

- **Real-time Web Dashboard** - Monitor trading activity, account balances, and performance metrics
- **Multiple Account Support** - Manage multiple MT5 trading accounts simultaneously  
- **Strategy Engine** - Built-in SMA crossover, RSI scalping, and hybrid trading strategies
- **Risk Management** - Dynamic position sizing, stop-loss/take-profit, and exposure controls
- **Backtesting** - Test strategies on historical data with comprehensive analytics
- **Notifications** - Email and SMS alerts for trade events and system status
- **WebSocket Integration** - Real-time updates without page refreshes

## Quick Start (Windows)

### Automatic Setup
1. Download the project files
2. Run `setup.bat` as Administrator
3. Follow the on-screen instructions
4. Use the desktop shortcut or run `start_windows.bat`

### Manual Setup
1. Install Python 3.8+ from https://python.org/downloads
2. Create virtual environment: `python -m venv venv`
3. Activate: `venv\Scripts\activate.bat`
4. Install packages: `install_requirements.bat`
5. Start server: `python start_with_eventlet.py`

## Access Points

- **Dashboard**: http://localhost:5000
- **Analytics**: http://localhost:5000/analytics
- **Backtesting**: http://localhost:5000/backtest  
- **Settings**: http://localhost:5000/settings

## Configuration

### Basic Setup
Edit `config.json` to configure your trading accounts:

```json
{
  "accounts": [
    {
      "name": "My MT5 Account",
      "login": 12345678,
      "server": "YourBroker-Demo",
      "password": "your_password",
      "enabled": true
    }
  ],
  "global_settings": {
    "sleep_seconds": 300,
    "risk_percentage": 1.0,
    "max_daily_trades": 10
  }
}
```

### Trading Control
Use `control.json` to pause/resume trading:
```json
{
  "status": "running",  // or "paused"
  "last_updated": "2025-01-01T00:00:00Z"
}
```

## File Structure

```
forex-trading-bot/
├── setup.bat                 # Complete Windows setup script
├── start_windows.bat          # Windows startup script
├── start_with_eventlet.py     # Recommended server start (best WebSocket support)
├── run_simple.py             # Development server
├── app.py                    # Flask application setup
├── main.py                   # Main entry point
├── models.py                 # Database models
├── routes.py                 # Web API endpoints
├── trading_engine.py         # Core trading logic
├── websocket_handler.py      # Real-time updates
├── config.json              # Trading configuration
├── control.json             # Bot control settings
├── troubleshooting.md       # Common issues and solutions
└── templates/               # Web interface templates
```

## Dependencies

### Core Requirements
- Flask 3.0.0
- Flask-SQLAlchemy 3.1.1
- Flask-SocketIO 5.3.6
- eventlet 0.33.3 (for WebSocket support)
- pandas 2.1.4 (data analysis)
- numpy 1.26.2 (calculations)

### Optional
- MetaTrader5 5.0.45 (for real trading)
- gunicorn (production server)

## Trading Modes

### Demo Mode (Default)
- No MetaTrader 5 required
- Uses mock data for testing
- Safe for learning and development

### Live Trading Mode
- Requires MetaTrader 5 installation
- Real broker account needed
- Configure credentials in config.json

## Troubleshooting

### WebSocket Issues
If you see "WebSocket disconnected" errors:
1. Use `start_with_eventlet.py` instead of other startup methods
2. Install eventlet: `pip install eventlet`
3. Check firewall settings for port 5000

### Database Issues  
If database errors occur:
1. Delete existing: `del forex_bot.db`
2. Restart the application to recreate

### Import Errors
If packages are missing:
1. Activate virtual environment: `venv\Scripts\activate.bat`
2. Run: `install_requirements.bat`

See `troubleshooting.md` for detailed solutions.

## Support

For issues or questions:
1. Check `troubleshooting.md` for common problems
2. Review console output for specific error messages  
3. Ensure all dependencies are properly installed
4. Verify MetaTrader 5 is running (for live trading)

## Security Notes

- Never commit real trading credentials to version control
- Use demo accounts for testing
- Set appropriate risk limits in configuration
- Monitor trading activity regularly

## License

This project is for educational and personal use. Trading involves risk - only trade with money you can afford to lose.