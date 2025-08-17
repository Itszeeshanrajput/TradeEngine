import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import logging
from app import db
from models import Trade

def _get_conversion_rate(profit_currency, account_currency):
    """
    Enhanced conversion rate calculation with better error handling
    """
    try:
        # Handle same currency
        if profit_currency == account_currency:
            return 1.0, False
            
        # Common broker suffixes to try
        suffixes = ['', 'm', '.pro', '_i', '.raw', '.m']
        
        # Try direct conversion
        for suffix in suffixes:
            symbol = f"{profit_currency}{account_currency}{suffix}"
            if mt5.symbol_select(symbol, True):
                tick = mt5.symbol_info_tick(symbol)
                if tick and tick.ask > 0:
                    logging.info(f"Found direct conversion rate via {symbol}: {tick.ask}")
                    return tick.ask, False
        
        # Try inverse conversion
        for suffix in suffixes:
            symbol = f"{account_currency}{profit_currency}{suffix}"
            if mt5.symbol_select(symbol, True):
                tick = mt5.symbol_info_tick(symbol)
                if tick and tick.ask > 0:
                    logging.info(f"Found inverse conversion rate via {symbol}: {tick.ask}")
                    return tick.ask, True
        
        # If no direct conversion found, try through USD
        if profit_currency != 'USD' and account_currency != 'USD':
            usd_rate_1, inverted_1 = _get_conversion_rate(profit_currency, 'USD')
            usd_rate_2, inverted_2 = _get_conversion_rate('USD', account_currency)
            
            if usd_rate_1 and usd_rate_2:
                if inverted_1:
                    usd_rate_1 = 1 / usd_rate_1
                if inverted_2:
                    usd_rate_2 = 1 / usd_rate_2
                
                combined_rate = usd_rate_1 * usd_rate_2
                logging.info(f"Calculated cross rate via USD: {combined_rate}")
                return combined_rate, False
        
        logging.warning(f"Could not find conversion rate for {profit_currency} -> {account_currency}")
        return None, False
        
    except Exception as e:
        logging.error(f"Error getting conversion rate: {e}")
        return None, False

def calculate_volume(symbol, sl_pips, risk_percent, max_volume, account_balance=None):
    """Enhanced volume calculation with better risk management"""
    try:
        account_info = mt5.account_info()
        symbol_info = mt5.symbol_info(symbol)
        
        if account_info is None or symbol_info is None:
            logging.error(f"[{symbol}] Could not get account/symbol info for volume calculation.")
            return max(0.01, symbol_info.volume_min if symbol_info else 0.01)
        
        balance = account_balance or account_info.balance
        risk_amount = balance * (risk_percent / 100)
        
        # Enhanced point calculation
        point = symbol_info.point
        if point == 0:
            logging.error(f"[{symbol}] Point value is zero")
            return max(0.01, symbol_info.volume_min)
        
        sl_in_price = sl_pips * point
        
        # Calculate pip value more accurately
        tick_value = symbol_info.trade_tick_value
        tick_size = symbol_info.trade_tick_size
        
        if tick_size > 0:
            pip_value = tick_value * (point / tick_size)
        else:
            pip_value = symbol_info.trade_contract_size * point
        
        # Currency conversion
        account_currency = account_info.currency
        profit_currency = symbol_info.currency_profit
        
        if profit_currency != account_currency:
            rate, inverted = _get_conversion_rate(profit_currency, account_currency)
            if rate is None:
                logging.error(f"[{symbol}] Could not find conversion rate")
                return max(0.01, symbol_info.volume_min)
            
            if inverted:
                pip_value = pip_value / rate
            else:
                pip_value = pip_value * rate
        
        # Calculate volume
        if pip_value <= 0:
            logging.error(f"[{symbol}] Calculated pip value is zero or negative")
            return max(0.01, symbol_info.volume_min)
        
        volume = risk_amount / (sl_pips * pip_value)
        
        # Apply constraints
        volume = max(symbol_info.volume_min, volume)
        volume = min(max_volume, volume)
        volume = min(volume, symbol_info.volume_max)
        
        # Round to step size
        if symbol_info.volume_step > 0:
            volume = round(volume / symbol_info.volume_step) * symbol_info.volume_step
        
        logging.info(f"[{symbol}] Volume calculation: Risk=${risk_amount:.2f}, SL={sl_pips} pips, Volume={volume:.3f}")
        
        return round(volume, 3)
        
    except Exception as e:
        logging.error(f"[{symbol}] Exception in volume calculation: {e}", exc_info=True)
        return 0.01

def get_dynamic_sltp(df, symbol, atr_period=14, sl_multiplier=1.5, tp_multiplier=2.0):
    """Enhanced dynamic SL/TP calculation with multiple methods"""
    try:
        if df is None or len(df) < atr_period + 5:
            logging.warning(f"[{symbol}] Not enough data for dynamic SL/TP calculation")
            return get_fallback_sltp(symbol)
        
        # Method 1: ATR-based
        atr_sl, atr_tp = _calculate_atr_sltp(df, symbol, atr_period, sl_multiplier, tp_multiplier)
        
        # Method 2: Support/Resistance based
        sr_sl, sr_tp = _calculate_support_resistance_sltp(df, symbol)
        
        # Method 3: Volatility percentile based
        vol_sl, vol_tp = _calculate_volatility_percentile_sltp(df, symbol)
        
        # Combine methods (use average)
        sl_pips = np.mean([atr_sl, sr_sl, vol_sl])
        tp_pips = np.mean([atr_tp, sr_tp, vol_tp])
        
        # Apply minimum and maximum constraints
        min_sl, max_sl = get_sl_constraints(symbol)
        min_tp, max_tp = get_tp_constraints(symbol)
        
        sl_pips = max(min_sl, min(max_sl, sl_pips))
        tp_pips = max(min_tp, min(max_tp, tp_pips))
        
        logging.info(f"[{symbol}] Dynamic SL/TP: SL={sl_pips:.1f} pips, TP={tp_pips:.1f} pips")
        
        return sl_pips, tp_pips
        
    except Exception as e:
        logging.error(f"[{symbol}] Error in dynamic SL/TP calculation: {e}")
        return get_fallback_sltp(symbol)

def _calculate_atr_sltp(df, symbol, period, sl_multiplier, tp_multiplier):
    """Calculate SL/TP based on ATR"""
    high_low = df['high'] - df['low']
    high_close = (df['high'] - df['close'].shift()).abs()
    low_close = (df['low'] - df['close'].shift()).abs()
    
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    atr = true_range.rolling(period).mean().iloc[-1]
    
    symbol_info = mt5.symbol_info(symbol)
    if not symbol_info or symbol_info.point == 0:
        return 20, 40
    
    point = symbol_info.point
    sl_in_price = atr * sl_multiplier
    tp_in_price = atr * tp_multiplier
    
    sl_pips = sl_in_price / point
    tp_pips = tp_in_price / point
    
    return sl_pips, tp_pips

def _calculate_support_resistance_sltp(df, symbol):
    """Calculate SL/TP based on nearby support/resistance levels"""
    try:
        # Find recent highs and lows
        window = 10
        df['high_peak'] = df['high'].rolling(window=window, center=True).max() == df['high']
        df['low_trough'] = df['low'].rolling(window=window, center=True).min() == df['low']
        
        current_price = df['close'].iloc[-1]
        
        # Find nearest resistance (above current price)
        resistance_levels = df[df['high_peak'] & (df['high'] > current_price)]['high'].tail(5)
        if not resistance_levels.empty:
            nearest_resistance = resistance_levels.min()
        else:
            nearest_resistance = current_price * 1.02  # 2% above
        
        # Find nearest support (below current price)
        support_levels = df[df['low_trough'] & (df['low'] < current_price)]['low'].tail(5)
        if not support_levels.empty:
            nearest_support = support_levels.max()
        else:
            nearest_support = current_price * 0.98  # 2% below
        
        symbol_info = mt5.symbol_info(symbol)
        if not symbol_info or symbol_info.point == 0:
            return 20, 40
        
        point = symbol_info.point
        
        # Calculate distances in pips
        resistance_distance = (nearest_resistance - current_price) / point
        support_distance = (current_price - nearest_support) / point
        
        # Use the smaller distance for SL, larger for TP
        sl_pips = min(resistance_distance, support_distance) * 0.8  # 80% of distance
        tp_pips = max(resistance_distance, support_distance) * 1.2  # 120% of distance
        
        return max(10, sl_pips), max(20, tp_pips)
        
    except Exception as e:
        logging.error(f"Error in support/resistance calculation: {e}")
        return 20, 40

def _calculate_volatility_percentile_sltp(df, symbol):
    """Calculate SL/TP based on volatility percentiles"""
    try:
        # Calculate daily ranges
        daily_ranges = (df['high'] - df['low']) / df['close'] * 100  # Percentage ranges
        
        # Use percentiles for SL/TP
        sl_percentile = daily_ranges.quantile(0.3)  # 30th percentile
        tp_percentile = daily_ranges.quantile(0.7)  # 70th percentile
        
        current_price = df['close'].iloc[-1]
        
        symbol_info = mt5.symbol_info(symbol)
        if not symbol_info or symbol_info.point == 0:
            return 20, 40
        
        point = symbol_info.point
        
        sl_price = current_price * (sl_percentile / 100)
        tp_price = current_price * (tp_percentile / 100)
        
        sl_pips = sl_price / point
        tp_pips = tp_price / point
        
        return max(10, sl_pips), max(20, tp_pips)
        
    except Exception as e:
        logging.error(f"Error in volatility percentile calculation: {e}")
        return 20, 40

def get_sl_constraints(symbol):
    """Get SL constraints based on symbol type"""
    if 'XAU' in symbol or 'GOLD' in symbol:
        return 50, 2000  # Gold: 50-2000 pips
    elif 'JPY' in symbol:
        return 5, 500    # JPY pairs: 5-500 pips
    elif any(crypto in symbol for crypto in ['BTC', 'ETH', 'ADA', 'SOL', 'XRP']):
        return 100, 5000  # Crypto: 100-5000 pips
    else:
        return 10, 1000   # Major pairs: 10-1000 pips

def get_tp_constraints(symbol):
    """Get TP constraints based on symbol type"""
    if 'XAU' in symbol or 'GOLD' in symbol:
        return 100, 4000  # Gold: 100-4000 pips
    elif 'JPY' in symbol:
        return 10, 1000   # JPY pairs: 10-1000 pips
    elif any(crypto in symbol for crypto in ['BTC', 'ETH', 'ADA', 'SOL', 'XRP']):
        return 200, 10000  # Crypto: 200-10000 pips
    else:
        return 20, 2000    # Major pairs: 20-2000 pips

def get_fallback_sltp(symbol):
    """Get fallback SL/TP values when calculation fails"""
    if 'XAU' in symbol or 'GOLD' in symbol:
        return 200, 400   # Gold
    elif 'JPY' in symbol:
        return 20, 40     # JPY pairs
    elif any(crypto in symbol for crypto in ['BTC', 'ETH', 'ADA', 'SOL', 'XRP']):
        return 500, 1000  # Crypto
    else:
        return 30, 60     # Major pairs

# Enhanced trade management functions
def _modify_position(position, sl, tp, comment):
    """Enhanced position modification with better error handling"""
    try:
        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "position": position.ticket,
            "sl": float(sl),
            "tp": float(tp),
            "comment": comment
        }
        
        result = mt5.order_send(request)
        
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            logging.info(f"Successfully modified position {position.ticket}: {comment} SL={sl:.5f}, TP={tp:.5f}")
            
            # Update database
            trade = Trade.query.filter_by(ticket=position.ticket).first()
            if trade:
                trade.sl = sl
                trade.tp = tp
                db.session.commit()
                
            return True
        else:
            logging.warning(f"Failed to modify position {position.ticket}: {result.comment}")
            return False
            
    except Exception as e:
        logging.error(f"Exception in _modify_position: {e}")
        return False

def update_trailing_stop(position, symbol, trail_pips=None, trail_percent=None):
    """Enhanced trailing stop with percentage and pip-based options"""
    try:
        if position.sl == 0:
            return False  # Don't trail if no initial SL
        
        symbol_info = mt5.symbol_info(symbol)
        tick = mt5.symbol_info_tick(symbol)
        
        if not symbol_info or not tick:
            return False
        
        point = symbol_info.point
        current_price = tick.bid if position.type == mt5.POSITION_TYPE_BUY else tick.ask
        
        # Calculate trail distance
        if trail_percent:
            trail_distance = current_price * (trail_percent / 100)
        elif trail_pips:
            trail_distance = trail_pips * point
        else:
            # Default to 1% or 20 pips, whichever is larger
            percent_distance = current_price * 0.01
            pip_distance = 20 * point
            trail_distance = max(percent_distance, pip_distance)
        
        new_sl = 0
        should_modify = False
        
        if position.type == mt5.POSITION_TYPE_BUY:
            new_sl = current_price - trail_distance
            # Only move SL up and only if trade is profitable
            if new_sl > position.price_open and new_sl > position.sl:
                should_modify = True
        
        elif position.type == mt5.POSITION_TYPE_SELL:
            new_sl = current_price + trail_distance
            # Only move SL down and only if trade is profitable
            if new_sl < position.price_open and new_sl < position.sl:
                should_modify = True
        
        if should_modify:
            return _modify_position(position, new_sl, position.tp, "Trailing Stop")
        
        return False
        
    except Exception as e:
        logging.error(f"Exception in update_trailing_stop: {e}")
        return False

def move_sl_to_breakeven(position, symbol, profit_threshold_pips=None, profit_threshold_percent=None):
    """Enhanced breakeven with flexible profit thresholds"""
    try:
        symbol_info = mt5.symbol_info(symbol)
        tick = mt5.symbol_info_tick(symbol)
        
        if not symbol_info or not tick:
            return False
        
        # Check if already at breakeven
        tolerance = 2 * symbol_info.point
        if abs(position.sl - position.price_open) <= tolerance:
            return False
        
        point = symbol_info.point
        current_price = tick.bid if position.type == mt5.POSITION_TYPE_BUY else tick.ask
        
        # Calculate profit threshold
        if profit_threshold_percent:
            threshold_distance = position.price_open * (profit_threshold_percent / 100)
        elif profit_threshold_pips:
            threshold_distance = profit_threshold_pips * point
        else:
            # Default thresholds based on symbol
            if 'XAU' in symbol:
                threshold_distance = 50 * point  # 50 pips for gold
            elif 'JPY' in symbol:
                threshold_distance = 15 * point  # 15 pips for JPY
            else:
                threshold_distance = 20 * point  # 20 pips for majors
        
        # Check if profit threshold is met
        profit_distance = 0
        should_move = False
        
        if position.type == mt5.POSITION_TYPE_BUY:
            profit_distance = current_price - position.price_open
            if profit_distance >= threshold_distance:
                should_move = True
        
        elif position.type == mt5.POSITION_TYPE_SELL:
            profit_distance = position.price_open - current_price
            if profit_distance >= threshold_distance:
                should_move = True
        
        if should_move:
            # Move to breakeven plus small buffer
            buffer = 2 * point
            breakeven_sl = position.price_open + (buffer if position.type == mt5.POSITION_TYPE_BUY else -buffer)
            return _modify_position(position, breakeven_sl, position.tp, "Breakeven SL")
        
        return False
        
    except Exception as e:
        logging.error(f"Exception in move_sl_to_breakeven: {e}")
        return False

def calculate_position_size_kelly(symbol, win_rate, avg_win, avg_loss, balance):
    """Calculate position size using Kelly Criterion"""
    try:
        if avg_loss <= 0 or win_rate <= 0 or win_rate >= 1:
            return 0.01
        
        # Kelly formula: f = (bp - q) / b
        # where b = avg_win/avg_loss, p = win_rate, q = 1 - win_rate
        b = avg_win / abs(avg_loss)
        p = win_rate
        q = 1 - win_rate
        
        kelly_fraction = (b * p - q) / b
        
        # Cap Kelly at 25% for safety
        kelly_fraction = min(kelly_fraction, 0.25)
        kelly_fraction = max(kelly_fraction, 0.01)
        
        # Convert to position size
        risk_amount = balance * kelly_fraction
        
        # Assume 1% risk per pip for calculation
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info and symbol_info.point > 0:
            volume = risk_amount / (100 * symbol_info.point * symbol_info.trade_contract_size)
            volume = max(symbol_info.volume_min, min(symbol_info.volume_max, volume))
            
            return round(volume, 2)
        
        return 0.01
        
    except Exception as e:
        logging.error(f"Error in Kelly position sizing: {e}")
        return 0.01
