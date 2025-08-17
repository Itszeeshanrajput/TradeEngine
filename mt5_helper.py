import MetaTrader5 as mt5
import pandas as pd
import logging
from app import db, socketio
from models import Trade, Account
from datetime import datetime
from notifications import NotificationManager

notification_manager = NotificationManager()

def initialize_mt5(login, password, server):
    """Initialize MT5 connection with enhanced error handling"""
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            if not mt5.initialize():
                raise RuntimeError(f"MT5 initialize failed: {mt5.last_error()}")
            
            if not mt5.login(login, password, server):
                raise RuntimeError(f"MT5 login failed for account {login}: {mt5.last_error()}")
            
            logging.info(f"Connected to MT5 account {login} on {server}")
            return True
            
        except Exception as e:
            retry_count += 1
            logging.warning(f"MT5 connection attempt {retry_count} failed: {e}")
            
            if retry_count < max_retries:
                import time
                time.sleep(5)  # Wait before retry
            else:
                raise e

def shutdown_mt5():
    """Shutdown MT5 connection"""
    mt5.shutdown()
    logging.info("MT5 connection shutdown.")

def get_data(symbol, timeframe, bars=200):
    """Get market data with error handling"""
    try:
        if not mt5.symbol_select(symbol, True):
            logging.warning(f"Could not select symbol {symbol}")
            return None
            
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, bars)
        
        if rates is None or len(rates) == 0:
            logging.warning(f"No data for {symbol} on timeframe {timeframe}")
            return None
            
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        return df
        
    except Exception as e:
        logging.error(f"Error getting data for {symbol}: {e}")
        return None

def place_order(symbol, order_type, volume, sl=None, tp=None, deviation=20, magic=123456, comment="auto_bot"):
    """Place order with database logging and notifications"""
    try:
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            logging.error(f"Could not get tick for {symbol}")
            return None

        order_type_mt5 = mt5.ORDER_TYPE_BUY if order_type == "buy" else mt5.ORDER_TYPE_SELL
        price = tick.ask if order_type == "buy" else tick.bid

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": float(volume),
            "type": order_type_mt5,
            "price": float(price),
            "sl": float(sl) if sl else 0.0,
            "tp": float(tp) if tp else 0.0,
            "deviation": deviation,
            "magic": magic,
            "comment": comment,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        result = mt5.order_send(request)
        
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            logging.error(f"Order send failed for {symbol}: {result.comment}")
            return None
        
        logging.info(f"Order sent successfully for {symbol}: Ticket #{result.order}")
        
        # Save trade to database
        save_trade_to_db(result, symbol, order_type, volume, price, sl, tp, comment)
        
        # Send notification
        trade_info = {
            'symbol': symbol,
            'type': order_type.upper(),
            'volume': volume,
            'price': price,
            'sl': sl,
            'tp': tp,
            'strategy': comment,
            'account': mt5.account_info().login if mt5.account_info() else 'Unknown'
        }
        notification_manager.send_trade_notification(trade_info)
        
        # Emit real-time update
        socketio.emit('new_trade', {
            'ticket': result.order,
            'symbol': symbol,
            'type': order_type.upper(),
            'volume': volume,
            'price': price,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        return result
        
    except Exception as e:
        logging.error(f"Exception in place_order for {symbol}: {e}", exc_info=True)
        return None

def save_trade_to_db(result, symbol, order_type, volume, price, sl, tp, comment):
    """Save trade to database"""
    try:
        account_info = mt5.account_info()
        if not account_info:
            return
        
        account = Account.query.filter_by(login=account_info.login).first()
        if not account:
            return
        
        trade = Trade(
            account_id=account.id,
            ticket=result.order,
            symbol=symbol,
            trade_type=order_type.upper(),
            volume=volume,
            price_open=price,
            sl=sl if sl else 0,
            tp=tp if tp else 0,
            status='OPEN',
            strategy=comment,
            comment=f"Opened by auto bot - {comment}"
        )
        
        db.session.add(trade)
        db.session.commit()
        
    except Exception as e:
        logging.error(f"Error saving trade to database: {e}")

def get_open_positions(symbol=None):
    """Get open positions with enhanced error handling"""
    try:
        positions = mt5.positions_get(symbol=symbol) if symbol else mt5.positions_get()
        return positions if positions else []
    except Exception as e:
        logging.error(f"Error getting open positions: {e}")
        return []

def close_position(position, comment="auto_close"):
    """Close position with database updates and notifications"""
    try:
        symbol = position.symbol
        is_buy = position.type == mt5.POSITION_TYPE_BUY
        order_type = mt5.ORDER_TYPE_SELL if is_buy else mt5.ORDER_TYPE_BUY
        tick = mt5.symbol_info_tick(symbol)
        
        if not tick:
            logging.error(f"Could not get tick for {symbol}")
            return None
            
        price = tick.bid if is_buy else tick.ask

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "position": position.ticket,
            "symbol": symbol,
            "volume": float(position.volume),
            "type": order_type,
            "price": float(price),
            "deviation": 20,
            "magic": 123456,
            "comment": comment,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        result = mt5.order_send(request)
        
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            logging.error(f"Failed to close position {position.ticket}: {result.comment}")
            return None
        
        logging.info(f"Successfully closed position {position.ticket}")
        
        # Update trade in database
        update_closed_trade_in_db(position, price)
        
        # Send notification
        duration = datetime.utcnow() - datetime.fromtimestamp(position.time)
        trade_info = {
            'symbol': symbol,
            'type': 'BUY' if is_buy else 'SELL',
            'volume': position.volume,
            'price_open': position.price_open,
            'price_close': price,
            'profit': position.profit,
            'duration': str(duration),
            'account': mt5.account_info().login if mt5.account_info() else 'Unknown'
        }
        notification_manager.send_trade_closed_notification(trade_info)
        
        # Emit real-time update
        socketio.emit('trade_closed', {
            'ticket': position.ticket,
            'symbol': symbol,
            'profit': position.profit,
            'close_price': price,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        return result
        
    except Exception as e:
        logging.error(f"Exception in close_position for {position.ticket}: {e}", exc_info=True)
        return None

def update_closed_trade_in_db(position, close_price):
    """Update closed trade in database"""
    try:
        trade = Trade.query.filter_by(ticket=position.ticket).first()
        if trade:
            trade.price_close = close_price
            trade.profit = position.profit
            trade.status = 'CLOSED'
            trade.close_time = datetime.utcnow()
            db.session.commit()
            
    except Exception as e:
        logging.error(f"Error updating closed trade in database: {e}")
