import time
import logging
import json
from datetime import datetime, time as dt_time
import MetaTrader5 as mt5
from app import app, db, socketio
from models import Trade, Account
import mt5_helper
import strategy
import risk_manager
from notifications import NotificationManager

class Trader:
    def __init__(self, account_config, global_settings):
        self.config = account_config
        self.globals = global_settings
        self.name = self.config.get('name', str(self.config['login']))
        self.timeframe = getattr(mt5, f"TIMEFRAME_{self.globals.get('timeframe', 'M30')}")
        self.notification_manager = NotificationManager()
        
        # Enhanced settings
        self.max_positions_per_symbol = self.config.get('max_positions_per_symbol', 1)
        self.max_total_positions = self.config.get('max_total_positions', 5)
        self.daily_loss_limit = self.config.get('daily_loss_limit', 5.0)  # Percentage
        self.enable_news_filter = self.config.get('enable_news_filter', False)
        
    def _get_control_status(self):
        """Check control status with enhanced error handling"""
        try:
            with open('control.json', 'r') as f:
                return json.load(f).get('status', 'running')
        except (FileNotFoundError, json.JSONDecodeError):
            # Create default control file
            try:
                with open('control.json', 'w') as f:
                    json.dump({'status': 'running'}, f)
                return 'running'
            except Exception:
                return 'running'
    
    def _update_dashboard_data(self):
        """Enhanced dashboard data update with error handling"""
        try:
            with app.app_context():
                acc_info = mt5.account_info()
                positions = mt5.positions_get()
                
                if acc_info:
                    # Update account in database
                    account = Account.query.filter_by(login=self.config['login']).first()
                    if account:
                        account.balance = acc_info.balance
                        account.equity = acc_info.equity
                        account.margin = acc_info.margin
                        account.margin_free = acc_info.margin_free
                        account.currency = acc_info.currency
                        account.updated_at = datetime.utcnow()
                        db.session.commit()
                
                # Prepare dashboard data
                dashboard_data = {'account_info': {}, 'positions': []}
                
                if acc_info:
                    dashboard_data['account_info'] = {
                        'balance': acc_info.balance,
                        'equity': acc_info.equity,
                        'margin': acc_info.margin,
                        'margin_free': acc_info.margin_free,
                        'currency': acc_info.currency,
                        'login': acc_info.login,
                        'server': acc_info.server
                    }
                
                if positions:
                    for pos in positions:
                        dashboard_data['positions'].append({
                            'ticket': pos.ticket,
                            'symbol': pos.symbol,
                            'type': "BUY" if pos.type == mt5.POSITION_TYPE_BUY else "SELL",
                            'volume': pos.volume,
                            'price_open': pos.price_open,
                            'price_current': pos.price_current,
                            'sl': pos.sl,
                            'tp': pos.tp,
                            'profit': pos.profit,
                            'swap': pos.swap,
                            'commission': pos.commission,
                            'time': datetime.fromtimestamp(pos.time).isoformat()
                        })
                
                # Write to file for backward compatibility
                with open('dashboard_data.json', 'w') as f:
                    json.dump(dashboard_data, f, indent=4)
                
                # Emit real-time update
                socketio.emit('dashboard_update', dashboard_data)
                
        except Exception as e:
            logging.error(f"Error updating dashboard data: {e}", exc_info=True)
    
    def _in_trading_session(self):
        """Enhanced trading session check"""
        if not self.globals.get("enable_time_filter", False):
            return True
            
        try:
            now = datetime.now().time()
            start = dt_time.fromisoformat(self.globals.get("trading_start", "07:00"))
            end = dt_time.fromisoformat(self.globals.get("trading_end", "17:00"))
            
            # Handle overnight sessions
            if start <= end:
                return start <= now <= end
            else:  # Overnight session (e.g., 22:00 to 06:00)
                return now >= start or now <= end
                
        except Exception as e:
            logging.error(f"Error checking trading session: {e}")
            return True  # Default to allowing trading
    
    def _check_daily_loss_limit(self):
        """Check if daily loss limit has been reached"""
        try:
            with app.app_context():
                today = datetime.utcnow().date()
                account = Account.query.filter_by(login=self.config['login']).first()
                
                if not account:
                    return False
                
                # Get today's closed trades
                today_trades = Trade.query.filter(
                    Trade.account_id == account.id,
                    Trade.status == 'CLOSED',
                    db.func.date(Trade.close_time) == today
                ).all()
                
                total_loss = sum(trade.profit for trade in today_trades if trade.profit < 0)
                loss_percentage = abs(total_loss) / account.balance * 100
                
                if loss_percentage >= self.daily_loss_limit:
                    logging.warning(f"Daily loss limit reached: {loss_percentage:.2f}%")
                    self.notification_manager.send_error_notification(
                        f"Daily loss limit reached for account {self.name}: {loss_percentage:.2f}%"
                    )
                    return True
                
                return False
                
        except Exception as e:
            logging.error(f"Error checking daily loss limit: {e}")
            return False
    
    def _check_position_limits(self, symbol):
        """Check position limits before opening new trades"""
        try:
            positions = mt5_helper.get_open_positions()
            
            # Check total positions limit
            if len(positions) >= self.max_total_positions:
                logging.info(f"Maximum total positions limit reached: {len(positions)}")
                return False
            
            # Check per-symbol position limit
            symbol_positions = [pos for pos in positions if pos.symbol == symbol]
            if len(symbol_positions) >= self.max_positions_per_symbol:
                logging.info(f"Maximum positions for {symbol} reached: {len(symbol_positions)}")
                return False
            
            return True
            
        except Exception as e:
            logging.error(f"Error checking position limits: {e}")
            return False
    
    def run_session(self):
        """Enhanced trading session with comprehensive error handling"""
        session_start_time = datetime.utcnow()
        
        # Check if bot is paused
        if self._get_control_status() == 'paused':
            logging.warning(f"Bot is PAUSED by user command. Skipping trading cycle for {self.name}.")
            try:
                mt5_helper.initialize_mt5(self.config['login'], self.config['password'], self.config['server'])
                self._update_dashboard_data()
                mt5_helper.shutdown_mt5()
            except Exception as e:
                logging.error(f"[{self.name}] Failed to update dashboard while paused: {e}")
            return
        
        # Check daily loss limit
        if self._check_daily_loss_limit():
            logging.warning(f"[{self.name}] Daily loss limit reached. Stopping trading for today.")
            return
        
        logging.info(f"--- Starting session for account: {self.name} ---")
        
        try:
            # Initialize MT5 connection
            mt5_helper.initialize_mt5(self.config['login'], self.config['password'], self.config['server'])
            
        except RuntimeError as e:
            logging.error(f"[{self.name}] MT5 initialization failed: {e}")
            self.notification_manager.send_error_notification(
                f"MT5 connection failed for account {self.name}: {str(e)}"
            )
            return
        
        try:
            # Update dashboard data
            self._update_dashboard_data()
            
            # Check trading session
            if not self._in_trading_session():
                logging.info(f"[{self.name}] Outside of trading session. Only managing existing positions.")
                self._manage_existing_positions_only()
                return
            
            # Process each symbol
            for symbol in self.config.get("symbols", []):
                try:
                    self._process_symbol(symbol)
                except Exception as e:
                    logging.error(f"[{self.name}/{symbol}] Error processing symbol: {e}", exc_info=True)
                    
                    # Send notification for symbol-specific errors
                    self.notification_manager.send_error_notification(
                        f"Error processing {symbol} on account {self.name}: {str(e)}"
                    )
            
            # Final dashboard update
            self._update_dashboard_data()
            
            session_duration = datetime.utcnow() - session_start_time
            logging.info(f"[{self.name}] Session completed in {session_duration.total_seconds():.2f} seconds")
            
        except Exception as e:
            logging.error(f"[{self.name}] Critical error in trading session: {e}", exc_info=True)
            self.notification_manager.send_error_notification(
                f"Critical trading session error for account {self.name}: {str(e)}"
            )
            
        finally:
            mt5_helper.shutdown_mt5()
            logging.info(f"--- Session finished for account: {self.name} ---")
    
    def _manage_existing_positions_only(self):
        """Manage existing positions without opening new ones"""
        try:
            for symbol in self.config.get("symbols", []):
                positions = mt5_helper.get_open_positions(symbol)
                for position in positions:
                    self._manage_position(position)
                    
        except Exception as e:
            logging.error(f"Error managing existing positions: {e}")
    
    def _process_symbol(self, symbol):
        """Enhanced symbol processing with comprehensive checks"""
        logging.info(f"[{self.name}/{symbol}] Processing...")
        
        try:
            # Get open positions for this symbol
            open_positions = mt5_helper.get_open_positions(symbol)
            
            # Manage existing positions
            for position in open_positions:
                self._manage_position(position)
            
            # Get market data
            df = mt5_helper.get_data(symbol, self.timeframe, bars=200)
            
            if df is None or len(df) < 50:
                logging.warning(f"[{self.name}/{symbol}] Insufficient market data (got {len(df) if df is not None else 0} bars)")
                return
            
            # Generate trading signal
            signal = strategy.get_signal(df, self.config.get("strategy_name", "sma_crossover"))
            last_price = df['close'].iloc[-1]
            
            logging.info(f"[{self.name}/{symbol}] Last Price: {last_price}, Signal: {signal}")
            
            # Check if we can open new positions
            if signal in ("buy", "sell") and len(open_positions) == 0:
                if self._check_position_limits(symbol):
                    self._execute_trade(symbol, signal, df, last_price)
                else:
                    logging.info(f"[{self.name}/{symbol}] Position limits prevent new trade")
            
        except Exception as e:
            logging.error(f"[{self.name}/{symbol}] Exception in _process_symbol: {e}", exc_info=True)
    
    def _manage_position(self, position):
        """Enhanced position management"""
        try:
            symbol = position.symbol
            logging.debug(f"[{self.name}/{symbol}] Managing position #{position.ticket}")
            
            # Update trailing stop
            trail_pips = self.config.get('trailing_stop_pips', 20)
            risk_manager.update_trailing_stop(position, symbol, trail_pips=trail_pips)
            
            # Move to breakeven if profitable
            breakeven_pips = self.config.get('breakeven_pips', 15)
            risk_manager.move_sl_to_breakeven(position, symbol, profit_threshold_pips=breakeven_pips)
            
            # Additional position management rules can be added here
            # e.g., time-based exits, partial closes, etc.
            
        except Exception as e:
            logging.error(f"Error managing position {position.ticket}: {e}")
    
    def _execute_trade(self, symbol, signal, df, last_price):
        """Enhanced trade execution with comprehensive risk management"""
        try:
            # Get dynamic SL/TP
            sl_pips, tp_pips = risk_manager.get_dynamic_sltp(df, symbol)
            
            # Calculate position size
            volume = risk_manager.calculate_volume(
                symbol, 
                sl_pips, 
                self.config['risk_percent'], 
                self.config['max_volume']
            )
            
            if volume <= 0:
                logging.warning(f"[{self.name}/{symbol}] Invalid volume calculated: {volume}")
                return
            
            # Get symbol info for price calculations
            symbol_info = mt5.symbol_info(symbol)
            if not symbol_info:
                logging.error(f"[{self.name}/{symbol}] Could not get symbol info")
                return
            
            # Calculate SL/TP prices
            if signal == "buy":
                sl = last_price - (sl_pips * symbol_info.point)
                tp = last_price + (tp_pips * symbol_info.point)
            else:  # sell
                sl = last_price + (sl_pips * symbol_info.point)
                tp = last_price - (tp_pips * symbol_info.point)
            
            # Validate prices
            if not self._validate_trade_prices(symbol, signal, last_price, sl, tp):
                logging.warning(f"[{self.name}/{symbol}] Trade prices validation failed")
                return
            
            # Log trade details
            strategy_name = self.config.get("strategy_name", "unknown")
            logging.info(f"[{self.name}/{symbol}] Placing {signal} order:")
            logging.info(f"  Volume: {volume}, Entry: {last_price:.5f}")
            logging.info(f"  SL: {sl:.5f} ({sl_pips:.1f} pips), TP: {tp:.5f} ({tp_pips:.1f} pips)")
            logging.info(f"  Strategy: {strategy_name}")
            
            # Execute the order
            result = mt5_helper.place_order(
                symbol=symbol,
                order_type=signal,
                volume=volume,
                sl=sl,
                tp=tp,
                comment=f"{strategy_name}_{self.name[:10]}"
            )
            
            if result:
                logging.info(f"[{self.name}/{symbol}] Trade executed successfully. Ticket: {result.order}")
                
                # Emit real-time notification
                socketio.emit('trade_opened', {
                    'account': self.name,
                    'symbol': symbol,
                    'type': signal.upper(),
                    'volume': volume,
                    'price': last_price,
                    'sl': sl,
                    'tp': tp,
                    'ticket': result.order,
                    'timestamp': datetime.utcnow().isoformat()
                })
            else:
                logging.error(f"[{self.name}/{symbol}] Trade execution failed")
                
        except Exception as e:
            logging.error(f"[{self.name}/{symbol}] Exception in _execute_trade: {e}", exc_info=True)
    
    def _validate_trade_prices(self, symbol, signal, entry_price, sl, tp):
        """Validate trade prices before execution"""
        try:
            symbol_info = mt5.symbol_info(symbol)
            if not symbol_info:
                return False
            
            # Check minimum distance from current price
            min_distance = symbol_info.trade_stops_level * symbol_info.point
            
            if signal == "buy":
                if abs(entry_price - sl) < min_distance:
                    logging.warning(f"SL too close to entry price for {symbol}")
                    return False
                if tp <= entry_price:
                    logging.warning(f"Invalid TP for buy order on {symbol}")
                    return False
            else:  # sell
                if abs(entry_price - sl) < min_distance:
                    logging.warning(f"SL too close to entry price for {symbol}")
                    return False
                if tp >= entry_price:
                    logging.warning(f"Invalid TP for sell order on {symbol}")
                    return False
            
            return True
            
        except Exception as e:
            logging.error(f"Error validating trade prices: {e}")
            return False
