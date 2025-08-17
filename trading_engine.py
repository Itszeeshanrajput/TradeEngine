import json
import time
import logging
import threading
from datetime import datetime
from app import app, db, socketio
from models import Account, Trade, SystemLog
try:
    from trader import Trader
except ImportError:
    # Mock Trader class for development
    class Trader:
        def __init__(self, account_config, global_settings=None):
            self.config = account_config
            self.global_settings = global_settings or {}
        
        def connect(self):
            return True
        
        def get_account_info(self):
            return {'balance': 10000, 'equity': 10000, 'margin': 0, 'margin_free': 10000}
        
        def get_open_positions(self):
            return []
        
        def check_signals_and_trade(self):
            return []
        
        def run_session(self):
            """Mock run session for development"""
            pass
from notifications import NotificationManager

class TradingEngine:
    def __init__(self):
        self.config = self.load_config()
        self.running = False
        self.notification_manager = NotificationManager()
        self.setup_logging()
    
    def setup_logging(self):
        """Setup database logging handler"""
        class DatabaseHandler(logging.Handler):
            def emit(self, record):
                with app.app_context():
                    try:
                        log_entry = SystemLog()
                        log_entry.level = record.levelname
                        log_entry.message = record.getMessage()
                        log_entry.module = record.module if hasattr(record, 'module') else record.name
                        db.session.add(log_entry)
                        db.session.commit()
                    except Exception:
                        pass  # Avoid infinite recursion in logging
        
        db_handler = DatabaseHandler()
        db_handler.setLevel(logging.INFO)
        logging.getLogger().addHandler(db_handler)
    
    def load_config(self):
        """Load configuration from file"""
        try:
            with open('config.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logging.error("Configuration file 'config.json' not found")
            return {"accounts": [], "global_settings": {}}
        except json.JSONDecodeError:
            logging.error("Error decoding 'config.json'")
            return {"accounts": [], "global_settings": {}}
    
    def get_control_status(self):
        """Check if trading is paused"""
        try:
            with open('control.json', 'r') as f:
                return json.load(f).get('status', 'running')
        except (FileNotFoundError, json.JSONDecodeError):
            return 'running'
    
    def sync_accounts(self):
        """Sync accounts from config to database"""
        with app.app_context():
            for account_config in self.config.get("accounts", []):
                existing_account = Account.query.filter_by(login=account_config['login']).first()
                
                if not existing_account:
                    account = Account()
                    account.name = account_config['name']
                    account.login = account_config['login']
                    account.server = account_config['server']
                    account.enabled = account_config.get('enabled', True)
                    db.session.add(account)
                else:
                    existing_account.name = account_config['name']
                    existing_account.server = account_config['server']
                    existing_account.enabled = account_config.get('enabled', True)
            
            db.session.commit()
    
    def start(self):
        """Start the trading engine"""
        self.running = True
        self.sync_accounts()
        
        while self.running:
            try:
                if self.get_control_status() == 'paused':
                    logging.info("Trading engine is paused")
                    time.sleep(30)
                    continue
                
                self.run_trading_cycle()
                
                sleep_interval = self.config.get("global_settings", {}).get("sleep_seconds", 300)
                logging.info(f"Trading cycle complete. Sleeping for {sleep_interval} seconds.")
                time.sleep(sleep_interval)
                
            except Exception as e:
                logging.error(f"Error in trading engine: {e}", exc_info=True)
                time.sleep(60)  # Wait a minute before retrying
    
    def run_trading_cycle(self):
        """Run one complete trading cycle"""
        with app.app_context():
            logging.info("Starting new trading cycle...")
            
            for account_config in self.config.get("accounts", []):
                if not account_config.get("enabled", False):
                    continue
                
                try:
                    trader = Trader(account_config, self.config.get("global_settings", {}))
                    if hasattr(trader, 'run_session'):
                        trader.run_session()
                    else:
                        # For mock trader, just connect and check status
                        trader.connect()
                    
                    # Update account info in database
                    self.update_account_info(account_config['login'])
                    
                    # Emit real-time updates
                    socketio.emit('account_updated', {
                        'login': account_config['login'],
                        'timestamp': datetime.utcnow().isoformat()
                    })
                    
                except Exception as e:
                    logging.error(f"Error processing account {account_config['login']}: {e}", exc_info=True)
                    
                    # Send notification for critical errors
                    self.notification_manager.send_error_notification(
                        f"Trading error on account {account_config['login']}: {str(e)}"
                    )
    
    def update_account_info(self, login):
        """Update account information in database"""
        try:
            import MetaTrader5 as mt5
            
            if mt5.terminal_info() is None:
                return
            
            account_info = mt5.account_info()
            if account_info:
                account = Account.query.filter_by(login=login).first()
                if account:
                    account.balance = account_info.balance
                    account.equity = account_info.equity
                    account.margin = account_info.margin
                    account.margin_free = account_info.margin_free
                    account.currency = account_info.currency
                    account.updated_at = datetime.utcnow()
                    db.session.commit()
        except ImportError:
            # MetaTrader5 not available in development environment
            logging.debug(f"MT5 not available, skipping account info update for {login}")
            pass
    
    def stop(self):
        """Stop the trading engine"""
        self.running = False
        logging.info("Trading engine stopped")
