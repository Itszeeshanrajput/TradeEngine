#!/usr/bin/env python3
"""
Simple development server runner without WebSocket complications
This bypasses gunicorn issues for development/demo purposes
"""

import threading
import time
import logging
from app import app, socketio
from trading_engine import TradingEngine

def start_trading_engine():
    """Start the trading engine in a separate thread"""
    time.sleep(2)  # Wait for app to start
    engine = TradingEngine()
    engine.start()

if __name__ == "__main__":
    # Start trading engine in background
    trading_thread = threading.Thread(target=start_trading_engine, daemon=True)
    trading_thread.start()
    
    # Start Flask-SocketIO development server
    print("Starting Forex Trading Bot Dashboard on http://0.0.0.0:5000")
    print("Dashboard: http://localhost:5000")
    print("Analytics: http://localhost:5000/analytics")
    print("Backtest: http://localhost:5000/backtest")
    print("Settings: http://localhost:5000/settings")
    
    # Use the development server which handles WebSockets better
    socketio.run(
        app, 
        host='0.0.0.0', 
        port=5000, 
        debug=False, 
        allow_unsafe_werkzeug=True,
        use_reloader=False
    )