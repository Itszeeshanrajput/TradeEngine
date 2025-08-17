import threading
import time
import logging
from app import app, socketio
from trading_engine import TradingEngine

def start_trading_engine():
    """Start the trading engine in a separate thread"""
    engine = TradingEngine()
    engine.start()

if __name__ == "__main__":
    # Start trading engine in background
    trading_thread = threading.Thread(target=start_trading_engine, daemon=True)
    trading_thread.start()
    
    # Start Flask-SocketIO server with eventlet
    print("Starting Forex Trading Bot Dashboard on http://0.0.0.0:5000")
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True, use_reloader=False, log_output=False)
