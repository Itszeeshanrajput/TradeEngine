# 💹 TradeEngine - Professional Forex Trading Bot

<div align="center">

**Automated Forex Trading Bot with Real-Time Dashboard & MetaTrader 5 Integration**

[![Python](https://img.shields.io/badge/Python-3.8+-blue?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0-black?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![MetaTrader5](https://img.shields.io/badge/MetaTrader-5-0066CC?style=for-the-badge&logo=metatrader5&logoColor=white)](https://www.metatrader5.com/)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=for-the-badge)](https://github.com/Itszeeshanrajput/TradeEngine)

**#ForexTrading #AutomatedTrading #TradingBot #Flask #MetaTrader5**

[Quick Start](#-quick-start) • [Features](#-features) • [Installation](#-installation) • [Documentation](#-documentation) • [Support](#-support)

</div>

---

## 📸 Features Showcase

### 🔥 NEW: Prop Firm Risk Management Mode
Easily pass challenges like FTMO, MyForexFunds, etc., with built-in strict risk management:
- **Daily Drawdown Limits:** Automatically stops trading if the daily loss limit is reached.
- **Max Total Drawdown:** Prevents catastrophic losses by halting bot completely if max drawdown hits.
- **Weekend/News Protection:** Disables trading during weekends and high-impact news.

### 📱 Telegram & Discord Notifications
Get real-time updates directly to your phone. Includes:
- Trade Opens / Closes
- Take Profit / Stop Loss hits
- Daily Summary & Profit/Loss reports

### 🎯 Core Capabilities
- **Real-time Web Dashboard** - Beautiful UI with **30-Day P&L Heatmap** (Like GitHub contributions but for money!)
- **Multi-Account Management** - Manage multiple MT5 accounts simultaneously
- **Automated Trading Engine** - Execute strategies 24/5 without manual intervention
- **Crypto & Forex Support** - Trade Major pairs, Gold, and Crypto (BTC/ETH) seamlessly.
- **Backtesting Suite** - Test strategies on historical data before live trading

### 🛡️ Safety & Security
- ✅ Demo mode for safe testing
- ✅ Configurable risk limits
- ✅ Automatic position monitoring
- ✅ Circuit breakers & safety stops
- ✅ Secure credential management

---

## 🚀 Quick Start (5 Minutes)

### Prerequisites
- Windows OS (MetaTrader 5 requirement)
- Python 3.8+
- MetaTrader 5 installed
- MT5 demo or live account

### Option 1: Automatic Setup (Windows)
```batch
# 1. Download and extract project
# 2. Open Command Prompt as Administrator
cd path\to\TradeEngine
setup.bat
```

### Option 2: Manual Setup
```bash
# Clone repository
git clone https://github.com/Itszeeshanrajput/TradeEngine.git
cd TradeEngine

# Create virtual environment
python -m venv venv
venv\Scripts\activate.bat

# Install dependencies
pip install -r requirements.txt

# Configure MT5 account
copy config.json.example config.json
# Edit config.json with your MT5 credentials

# Run the bot
python start_with_eventlet.py
```

### Access the Dashboard
```
🌐 Dashboard:     http://localhost:5000
📊 Analytics:     http://localhost:5000/analytics
🧪 Backtesting:   http://localhost:5000/backtest
⚙️  Settings:      http://localhost:5000/settings
```

---

## 📖 Documentation

### 📋 Table of Contents
- [Features](#-features)
- [Installation](#-installation)
- [Configuration](#%EF%B8%8F-configuration)
- [Usage Guide](#-usage-guide)
- [API Reference](#-api-reference)
- [Strategies](#-trading-strategies)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)

---

## ⚙️ Configuration

### config.json Setup

```json
{
  "accounts": [
    {
      "name": "Primary Trading Account",
      "login": 262323581,
      "password": "your_password",
      "server": "Exness-MT5Trial16",
      "enabled": true,
      "strategy": "sma_crossover",
      "risk_percentage": 2.0
    }
  ],
  "global_settings": {
    "sleep_seconds": 300,
    "max_daily_trades": 10,
    "max_drawdown_percent": 5.0,
    "timezone": "UTC"
  },
  "notifications": {
    "email_enabled": false,
    "sms_enabled": false,
    "discord_webhook": null
  }
}
```

### control.json (Runtime Control)

```json
{
  "status": "running",
  "last_updated": "2026-08-31T12:00:00Z",
  "pause_reason": null
}
```

Toggle between `"running"`, `"paused"`, and `"stopped"` to control the bot.

---

## 🎮 Usage Guide

### Starting the Bot

```bash
# Option 1: With WebSocket support (Recommended)
python start_with_eventlet.py

# Option 2: Simple development server
python run_simple.py

# Option 3: Production with gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Dashboard Features

1. **Account Overview**
   - Real-time balance & equity
   - Open positions & P&L
   - Account statistics

2. **Trading Control**
   - Place manual orders
   - Close positions
   - Modify take-profit/stop-loss

3. **Analytics Panel**
   - Win rate & profit factor
   - Drawdown analysis
   - Monthly performance chart

4. **Backtesting Engine**
   - Upload historical data
   - Run strategy simulations
   - Export reports

5. **Settings**
   - Configure trading parameters
   - Manage accounts
   - Adjust risk limits

---

## 🤖 Trading Strategies

### 1. SMA Crossover (Trend Following)
```python
# Fast MA crosses above/below Slow MA
fast_period = 10
slow_period = 20
signal = "BUY when fast > slow"
```
- Best for: Trending markets
- Timeframe: 1H, 4H

### 2. RSI Scalping (Mean Reversion)
```python
# Trade oversold/overbought levels
rsi_period = 14
oversold = 30
overbought = 70
```
- Best for: Range-bound markets
- Timeframe: 5M, 15M

### 3. Hybrid Strategy
- Combines trend confirmation with momentum
- Best for: All market conditions
- Timeframe: 1H+

---

## 🧪 Backtesting

### Run a Strategy Backtest

```python
from backtester import Backtester
import pandas as pd

# Initialize backtester
bt = Backtester()

# Load historical data
df = pd.read_csv('EURUSD_H1.csv')

# Run SMA Crossover backtest
results = bt.backtest_sma_crossover(
    df,
    fast_period=10,
    slow_period=20,
    initial_capital=10000,
    lot_size=0.1,
    stop_loss=50,
    take_profit=100
)

# View results
print(f"Total Trades: {results['total_trades']}")
print(f"Win Rate: {results['win_rate']:.2f}%")
print(f"Profit Factor: {results['profit_factor']:.2f}")
print(f"Max Drawdown: {results['max_drawdown']:.2f}%")
```

---

## 🔧 Troubleshooting

### Common Issues & Solutions

**1. "MT5 Connection Failed"**
```
✅ Solution:
- Verify MetaTrader 5 is running
- Check credentials in config.json
- Ensure broker server name is correct
- Enable DLL imports in MT5: Tools → Options → Expert Advisors → Allow DLL imports
```

**2. "Port 5000 Already in Use"**
```bash
# Find process using port 5000
netstat -ano | findstr :5000

# Kill the process (replace PID with actual)
taskkill /PID <PID> /F

# Or change port in start_with_eventlet.py
# uvicorn.run(app, host="0.0.0.0", port=8001)
```

**3. "WebSocket Disconnected"**
```
✅ Solution:
- Use start_with_eventlet.py (best WebSocket support)
- Check firewall allows port 5000
- Disable VPN temporarily
- Restart application
```

**4. "Database Locked"**
```bash
# Delete database and restart
del forex_bot.db
python start_with_eventlet.py
```

**5. "Symbol Not Found"**
```
✅ Solution:
- Check MT5 available symbols list
- Try different symbol names: "EURUSD", "EURUSDm", "EURUSD.m"
- Verify symbol is tradeable on your broker
```

---

## 📁 Project Structure

```
TradeEngine/
├── setup.bat                    # Windows automated setup
├── start_windows.bat            # Windows startup shortcut
├── start_with_eventlet.py       # Production server (RECOMMENDED)
├── run_simple.py               # Development server
├── app.py                      # Flask application factory
├── main.py                     # Entry point
├── models.py                   # Database models
├── routes.py                   # API endpoints
├── trading_engine.py           # Core trading logic
├── websocket_handler.py        # Real-time communications
├── backtester.py              # Strategy backtesting
├── config.json                # Trading configuration
├── control.json               # Bot control settings
├── requirements.txt           # Python dependencies
├── templates/                 # HTML templates
│   ├── index.html            # Dashboard
│   ├── analytics.html        # Analytics page
│   ├── backtest.html         # Backtesting UI
│   └── settings.html         # Settings page
├── static/                    # CSS, JS, images
├── database/                  # SQLite database
├── logs/                      # Application logs
└── README.md                 # This file
```

---

## 📦 Dependencies

### Core Requirements
```
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
Flask-SocketIO==5.3.6
eventlet==0.33.3
pandas==2.1.4
numpy==1.26.2
requests==2.31.0
python-dotenv==1.0.0
```

### Optional (For Live Trading)
```
MetaTrader5==5.0.45
```

### Install All
```bash
pip install -r requirements.txt
```

---

## ⚠️ Important Warnings

### ⚡ Risk Disclaimer
Trading forex and CFDs carries significant risk and may not be suitable for all investors. You could lose more than your initial investment.

- ⚠️ **Always use a demo account first** for testing
- ⚠️ **Never risk money you cannot afford to lose**
- ⚠️ **Use proper risk management** (position sizing, stop-loss)
- ⚠️ **Backtest thoroughly** before live trading
- ⚠️ **Past performance ≠ future results**

### 🔒 Security Best Practices
- 🚫 Never commit real trading credentials to git
- 🔐 Use `.env` files for sensitive data
- 🔏 Keep MT5 password secure
- 📋 Regularly review trading logs
- ✅ Enable two-factor authentication on broker account

---

## 🤝 Contributing

We welcome contributions! Here's how to help:

### Development Setup
```bash
git clone https://github.com/Itszeeshanrajput/TradeEngine.git
cd TradeEngine
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
```

### Making Changes
1. Create a feature branch: `git checkout -b feature/amazing-feature`
2. Make your changes
3. Test thoroughly
4. Commit: `git commit -m 'Add amazing feature'`
5. Push: `git push origin feature/amazing-feature`
6. Open a Pull Request

### Areas for Contribution
- 🐛 Bug fixes and stability improvements
- ✨ New trading strategies
- 📊 Additional analytics metrics
- 🎨 UI/UX improvements
- 📝 Documentation enhancements
- 🧪 Test coverage expansion

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

**Important:** This software is for educational and personal use. Trading involves significant risk. The authors are not responsible for trading losses.

---

## 📞 Support & Contact

### Get Help
- 📖 [Read Full Documentation](docs/)
- 🐛 [Report a Bug](https://github.com/Itszeeshanrajput/TradeEngine/issues)
- 💡 [Request a Feature](https://github.com/Itszeeshanrajput/TradeEngine/issues)
- 📧 **Email:** itszeeshanrajput@gmail.com
- 🔗 **GitHub:** [@Itszeeshanrajput](https://github.com/Itszeeshanrajput)

### Community
- 💬 GitHub Discussions (coming soon)
- 🐦 Follow for updates
- ⭐ Star this repo if it helps you!

---

## 🙏 Acknowledgments

- [MetaTrader 5](https://www.metatrader5.com/) - Trading platform
- [Flask](https://flask.palletsprojects.com/) - Web framework
- [Pandas](https://pandas.pydata.org/) - Data analysis
- [Flask-SocketIO](https://flask-socketio.readthedocs.io/) - Real-time features

---

<div align="center">

### ⭐ If this project helps you, please give it a star!

**Made with ❤️ for the trading community**

[🔝 Back to Top](#-tradeengine---professional-forex-trading-bot)

</div>