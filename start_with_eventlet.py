#!/usr/bin/env python3
"""
Start the Forex Trading Bot with eventlet for better WebSocket support
"""

import os
import threading
import time
import logging
import eventlet

# Patch everything before importing other modules
eventlet.monkey_patch()

from app import app, socketio
from trading_engine import TradingEngine

def start_trading_engine():
    """Start the trading engine in a separate thread"""
    time.sleep(3)  # Wait for app to start
    engine = TradingEngine()
    engine.start()

if __name__ == "__main__":
    # Set environment variables if not set
    os.environ.setdefault("SESSION_SECRET", "forex-trading-bot-secret-key-2025")
    os.environ.setdefault("DATABASE_URL", "sqlite:///forex_bot.db")
    
    # Start trading engine in background
    trading_thread = threading.Thread(target=start_trading_engine, daemon=True)
    trading_thread.start()
    
    # Start Flask-SocketIO server with eventlet
    print("Starting Forex Trading Bot Dashboard with eventlet...")
    print("Dashboard: http://localhost:5000")
    print("Analytics: http://localhost:5000/analytics")
    print("Backtest: http://localhost:5000/backtest")
    print("Settings: http://localhost:5000/settings")
    print()
    print("Press Ctrl+C to stop the server")
    
    try:
        socketio.run(
            app, 
            host='0.0.0.0', 
            port=5000, 
            debug=False,
            use_reloader=False,
            log_output=True
        )
    except KeyboardInterrupt:
        print("\nShutting down server...")
    except Exception as e:
        print(f"Server error: {e}")
        logging.error(f"Server startup error: {e}", exc_info=True)