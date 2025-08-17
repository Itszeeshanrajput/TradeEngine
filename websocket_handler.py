from flask_socketio import emit, disconnect
from app import socketio, app
import json
import logging

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logging.info("Client connected to WebSocket")
    emit('status', {'status': 'connected'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logging.info("Client disconnected from WebSocket")

@socketio.on('subscribe_to_updates')
def handle_subscribe(data):
    """Handle subscription to real-time updates"""
    update_type = data.get('type', 'all')
    logging.info(f"Client subscribed to {update_type} updates")
    emit('subscription_confirmed', {'type': update_type})

@socketio.on('get_bot_status')
def handle_bot_status():
    """Get current bot status"""
    try:
        with open('control.json', 'r') as f:
            status = json.load(f).get('status', 'running')
        emit('bot_status', {'status': status})
    except Exception:
        emit('bot_status', {'status': 'unknown'})

def emit_trade_update(trade_data):
    """Emit trade update to all connected clients"""
    with app.app_context():
        socketio.emit('trade_update', trade_data)

def emit_account_update(account_data):
    """Emit account update to all connected clients"""
    with app.app_context():
        socketio.emit('account_update', account_data)

def emit_system_log(log_data):
    """Emit system log to all connected clients"""
    with app.app_context():
        socketio.emit('system_log', log_data)
