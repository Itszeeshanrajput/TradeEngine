import MetaTrader5 as mt5
import pandas as pd
import logging

def initialize_mt5(login, password, server):
    if not mt5.initialize():
        raise RuntimeError(f"MT5 initialize failed: {mt5.last_error()}")
    if not mt5.login(login, password, server):
        raise RuntimeError(f"MT5 login failed for account {login}: {mt5.last_error()}")
    logging.info(f"Connected to MT5 account {login} on {server}")

def shutdown_mt5():
    mt5.shutdown()
    logging.info("MT5 connection shutdown.")

def get_data(symbol, timeframe, bars=200):
    if not mt5.symbol_select(symbol, True):
        logging.warning(f"Could not select symbol {symbol}")
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, bars)
    if rates is None or len(rates) == 0:
        logging.warning(f"No data for {symbol} on timeframe {timeframe}")
        return None
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    return df

def place_order(symbol, order_type, volume, sl=None, tp=None, deviation=20, magic=123456):
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        logging.error(f"Could not get tick for {symbol}")
        return None

    order_type_mt5 = mt5.ORDER_TYPE_BUY if order_type == "buy" else mt5.ORDER_TYPE_SELL
    price = tick.ask if order_type == "buy" else tick.bid

    request = {
        "action": mt5.TRADE_ACTION_DEAL, "symbol": symbol, "volume": float(volume),
        "type": order_type_mt5, "price": float(price),
        "sl": float(sl) if sl else 0.0, "tp": float(tp) if tp else 0.0,
        "deviation": deviation, "magic": magic, "comment": "auto_bot",
        "type_time": mt5.ORDER_TIME_GTC, "type_filling": mt5.ORDER_FILLING_IOC,
    }
    
    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        logging.error(f"Order send failed for {symbol}: {result.comment}")
        return None
    logging.info(f"Order sent successfully for {symbol}: Ticket #{result.order}")
    return result

def get_open_positions(symbol=None):
    positions = mt5.positions_get(symbol=symbol) if symbol else mt5.positions_get()
    return positions if positions else []

def close_position(position):
    symbol = position.symbol
    is_buy = position.type == mt5.POSITION_TYPE_BUY
    order_type = mt5.ORDER_TYPE_SELL if is_buy else mt5.ORDER_TYPE_BUY
    tick = mt5.symbol_info_tick(symbol)
    price = tick.bid if is_buy else tick.ask

    request = {
        "action": mt5.TRADE_ACTION_DEAL, "position": position.ticket, "symbol": symbol,
        "volume": float(position.volume), "type": order_type, "price": float(price),
        "deviation": 20, "magic": 123456, "comment": "auto_close",
        "type_time": mt5.ORDER_TIME_GTC, "type_filling": mt5.ORDER_FILLING_IOC,
    }
    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        logging.error(f"Failed to close position {position.ticket}: {result.comment}")
    else:
        logging.info(f"Successfully closed position {position.ticket}")
    return result