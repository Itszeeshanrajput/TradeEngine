import MetaTrader5 as mt5
import pandas as pd
import logging

def _get_conversion_rate(profit_currency, account_currency):
    """
    Finds the conversion rate between two currencies, handling broker suffixes.
    Returns the rate and whether the calculation needs to be inverted.
    """
    for suffix in ['', 'm', '.pro', '_i']: # Common suffixes
        symbol = f"{profit_currency}{account_currency}{suffix}"
        if mt5.symbol_select(symbol, True):
            tick = mt5.symbol_info_tick(symbol)
            if tick and tick.ask > 0:
                logging.info(f"Found direct conversion rate via {symbol}")
                return tick.ask, False # Not inverted
    
    for suffix in ['', 'm', '.pro', '_i']:
        symbol = f"{account_currency}{profit_currency}{suffix}"
        if mt5.symbol_select(symbol, True):
            tick = mt5.symbol_info_tick(symbol)
            if tick and tick.ask > 0:
                logging.info(f"Found inverse conversion rate via {symbol}")
                return tick.ask, True # Inverted
                
    return None, False

def calculate_volume(symbol, sl_pips, risk_percent, max_volume):
    # This function remains unchanged from the last version
    try:
        account_info = mt5.account_info()
        symbol_info = mt5.symbol_info(symbol)
        if account_info is None or symbol_info is None:
            logging.error(f"[{symbol}] Could not get account/symbol info for volume calculation.")
            return 0.01
        balance = account_info.balance
        risk_amount = balance * (risk_percent / 100)
        sl_in_price = sl_pips * symbol_info.point
        loss_per_lot_in_profit_currency = sl_in_price * symbol_info.trade_contract_size
        account_currency = account_info.currency
        profit_currency = symbol_info.currency_profit
        if profit_currency == account_currency:
            loss_per_lot_in_account_currency = loss_per_lot_in_profit_currency
        else:
            rate, inverted = _get_conversion_rate(profit_currency, account_currency)
            if rate is None:
                logging.error(f"[{symbol}] Could not find conversion pair for {profit_currency} -> {account_currency}.")
                return 0.01
            if inverted:
                loss_per_lot_in_account_currency = loss_per_lot_in_profit_currency / rate
            else:
                loss_per_lot_in_account_currency = loss_per_lot_in_profit_currency * rate
        if loss_per_lot_in_account_currency <= 0:
            logging.error(f"[{symbol}] Calculated loss per lot is zero or negative. Cannot calculate volume.")
            return 0.01
        volume = risk_amount / loss_per_lot_in_account_currency
        volume = max(symbol_info.volume_min, volume)
        volume = min(max_volume, volume)
        if symbol_info.volume_step != 0:
            volume = round(volume / symbol_info.volume_step) * symbol_info.volume_step
        logging.info(f"[{symbol}] Volume calculation: RiskAmount={risk_amount:.2f} {account_currency}, LossPerLot={loss_per_lot_in_account_currency:.2f} {account_currency}")
        return round(volume, 2)
    except Exception as e:
        logging.error(f"[{symbol}] An exception occurred during volume calculation: {e}", exc_info=True)
        return 0.01

def get_dynamic_sltp(df, symbol, pips_multiplier=1.5):
    # This function remains unchanged
    if df is None or len(df) < 15:
        logging.warning(f"[{symbol}] Not enough data for ATR calculation. Using fixed SL/TP.")
        return 20, 40
    high_low = df['high'] - df['low']
    high_close = (df['high'] - df['close'].shift()).abs()
    low_close = (df['low'] - df['close'].shift()).abs()
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    atr = true_range.rolling(14).mean().iloc[-1]
    symbol_info = mt5.symbol_info(symbol)
    if not symbol_info: return 20, 40
    point = symbol_info.point
    if point == 0: return 20, 40
    sl_in_price = atr * pips_multiplier
    sl_pips = sl_in_price / point
    tp_pips = sl_pips * 2
    logging.info(f"[{symbol}] ATR calculation: ATR={atr:.5f}, SL Pips={sl_pips:.1f}, TP Pips={tp_pips:.1f}")
    return sl_pips, tp_pips

# --- NEW AND IMPLEMENTED TRADE MANAGEMENT FUNCTIONS ---

def _modify_position(position, sl, tp, comment):
    """Helper function to send the SL/TP modification request."""
    request = {
        "action": mt5.TRADE_ACTION_SLTP,
        "position": position.ticket,
        "sl": float(sl),
        "tp": float(tp),
        "comment": comment
    }
    result = mt5.order_send(request)
    if result.retcode == mt5.TRADE_RETCODE_DONE:
        logging.info(f"Successfully modified position {position.ticket}: {comment} to SL={sl:.5f}, TP={tp:.5f}")
    else:
        logging.warning(f"Failed to modify position {position.ticket}: {result.comment}")
    return result

def update_trailing_stop(position, symbol, trail_pips=20):
    """If a trade is in profit, this function trails the stop loss behind the price."""
    if position.sl == 0: return # Don't trail if there's no initial SL

    point = mt5.symbol_info(symbol).point
    tick = mt5.symbol_info_tick(symbol)
    if not tick: return

    new_sl = 0

    if position.type == mt5.POSITION_TYPE_BUY:
        price = tick.bid
        new_sl = price - (trail_pips * point)
        # Only move the SL up, and only if it's profitable
        if new_sl > position.price_open and new_sl > position.sl:
            _modify_position(position, new_sl, position.tp, "Trailing Stop")

    elif position.type == mt5.POSITION_TYPE_SELL:
        price = tick.ask
        new_sl = price + (trail_pips * point)
        # Only move the SL down, and only if it's profitable
        if new_sl < position.price_open and new_sl < position.sl:
            _modify_position(position, new_sl, position.tp, "Trailing Stop")

def move_sl_to_breakeven(position, symbol, profit_pips=15):
    """Once a trade is in profit by a certain amount, move the SL to the entry price."""
    point = mt5.symbol_info(symbol).point
    tick = mt5.symbol_info_tick(symbol)
    if not tick: return
    
    # Check if SL is already at or past the entry price
    if (position.type == mt5.POSITION_TYPE_BUY and position.sl >= position.price_open) or \
       (position.type == mt5.POSITION_TYPE_SELL and position.sl != 0 and position.sl <= position.price_open):
        return

    current_price = tick.bid if position.type == mt5.POSITION_TYPE_BUY else tick.ask
    profit_in_price = profit_pips * point
    
    # If profit threshold is met, move SL to entry price
    if (position.type == mt5.POSITION_TYPE_BUY and current_price >= position.price_open + profit_in_price) or \
       (position.type == mt5.POSITION_TYPE_SELL and current_price <= position.price_open - profit_in_price):
        _modify_position(position, position.price_open, position.tp, "Breakeven SL")