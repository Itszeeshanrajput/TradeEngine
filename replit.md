# Overview

This is a comprehensive automated Forex trading bot application built with Flask and MetaTrader 5 integration. The system manages multiple trading accounts simultaneously, executes trades based on configurable strategies, and provides a real-time web dashboard for monitoring and control. The bot supports various trading strategies (SMA crossover, RSI scalping, hybrid approaches), implements sophisticated risk management, and includes backtesting capabilities for strategy validation.

## Recent Changes (August 2025)
- Fixed main.py socketio.run() parameter issues 
- Resolved trading_engine.py model constructor problems
- Improved WebSocket configuration for better stability
- Created comprehensive Windows setup automation with setup.bat
- Added multiple startup methods (start_with_eventlet.py recommended)
- Implemented troubleshooting documentation and recovery procedures

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture
- **Web Dashboard**: Flask-based web application with real-time updates via WebSocket connections
- **Template System**: Jinja2 templates with Bootstrap dark theme for responsive UI
- **JavaScript Components**: Modular client-side scripts for charts (Chart.js), WebSocket management, and real-time data visualization
- **Static Assets**: CSS styling with custom trading-themed color schemes and interactive elements

## Backend Architecture
- **Flask Application**: Main web server handling HTTP requests and WebSocket connections
- **Trading Engine**: Multi-threaded background service managing all trading operations
- **Strategy System**: Modular strategy implementations (SMA crossover, RSI scalping, combined strategies) with pluggable architecture
- **Risk Manager**: Dynamic position sizing, stop-loss/take-profit calculation, and exposure management
- **MT5 Integration**: Direct MetaTrader 5 API connection for market data and trade execution

## Data Storage
- **SQLAlchemy ORM**: Database abstraction layer with SQLite as default database
- **Models**: Account management, trade tracking, backtest results, and system logging
- **Configuration Management**: JSON-based configuration files for accounts, strategies, and system settings
- **Real-time State**: JSON files for control commands and dashboard data persistence

## Authentication & Security
- **Session Management**: Flask sessions with configurable secret keys
- **MT5 Authentication**: Secure credential storage in configuration files
- **Environment Variables**: Sensitive data (database URLs, API keys) managed through environment variables
- **Proxy Support**: Built-in proxy fix middleware for deployment flexibility

## Trading System Design
- **Multi-Account Support**: Simultaneous management of multiple MT5 accounts with independent configurations
- **Strategy Engine**: Pluggable strategy system supporting technical indicators and custom logic
- **Risk Management**: Per-trade and account-level risk controls with dynamic position sizing
- **Order Management**: Comprehensive order placement, modification, and tracking system
- **Real-time Monitoring**: Live position tracking with P&L calculation and performance metrics

## Background Services
- **Trading Thread**: Daemon thread running continuous trading operations
- **WebSocket Handler**: Real-time communication between backend and frontend
- **Notification System**: Email and SMS notifications for trade events and system alerts
- **Backtesting Engine**: Historical data analysis and strategy performance validation

# External Dependencies

## Core Framework Dependencies
- **Flask**: Web application framework with SQLAlchemy ORM integration
- **Flask-SocketIO**: WebSocket support for real-time bidirectional communication
- **MetaTrader 5 API**: Direct integration with MT5 terminal for market data and trade execution

## Data Analysis & Processing
- **Pandas**: Financial data manipulation and technical indicator calculations
- **NumPy**: Numerical computations for strategy algorithms and risk calculations
- **Chart.js**: Frontend charting library for trading performance visualization

## Notification Services
- **SMTP Integration**: Email notifications via configurable SMTP servers
- **Twilio API**: SMS notifications for critical trading events (optional)

## Database & Storage
- **SQLite**: Default database engine with PostgreSQL support available
- **JSON Configuration**: File-based configuration management for flexibility
- **File System**: Dashboard data persistence and control state management

## Development & Deployment
- **Werkzeug**: WSGI utilities with proxy fix middleware for production deployment
- **Threading**: Python threading for concurrent trading operations and web serving
- **Environment Configuration**: Support for various deployment environments through environment variables

## Market Data & Trading
- **MetaTrader 5 Terminal**: Required installation for market connectivity and trade execution
- **Broker Integration**: Compatible with MT5-supporting brokers (configured for Exness demo accounts)
- **Real-time Data Feeds**: Live market data for multiple currency pairs and instruments