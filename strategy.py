import pandas as pd
import numpy as np
import logging

def _sma_crossover_signal(df):
    """Generates a signal based on a 10/20 SMA crossover with additional filters"""
    try:
        df['SMA10'] = df['close'].rolling(window=10).mean()
        df['SMA20'] = df['close'].rolling(window=20).mean()
        
        # Add volume filter if available
        if 'tick_volume' in df.columns:
            df['avg_volume'] = df['tick_volume'].rolling(window=20).mean()
            volume_filter = df['tick_volume'].iloc[-1] > df['avg_volume'].iloc[-1] * 1.2
        else:
            volume_filter = True

        last_row = df.iloc[-1]
        prev_row = df.iloc[-2]

        if pd.isna(last_row['SMA10']) or pd.isna(last_row['SMA20']):
            return "hold"
        
        # Check for crossover with volume confirmation
        if (prev_row['SMA10'] <= prev_row['SMA20'] and 
            last_row['SMA10'] > last_row['SMA20'] and volume_filter):
            logging.info("SMA Crossover: Bullish signal with volume confirmation")
            return "buy"
        elif (prev_row['SMA10'] >= prev_row['SMA20'] and 
              last_row['SMA10'] < last_row['SMA20'] and volume_filter):
            logging.info("SMA Crossover: Bearish signal with volume confirmation")
            return "sell"
        else:
            return "hold"
            
    except Exception as e:
        logging.error(f"Error in SMA crossover strategy: {e}")
        return "hold"

def _rsi_scalping_signal(df):
    """Enhanced RSI scalping with momentum confirmation"""
    try:
        # Calculate RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        
        if loss.sum() == 0:
            return "hold"
            
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # Add momentum filter
        df['momentum'] = df['close'] - df['close'].shift(5)
        
        last_rsi = df['RSI'].iloc[-1]
        momentum = df['momentum'].iloc[-1]

        if pd.isna(last_rsi):
            return "hold"
        
        # Enhanced RSI signals with momentum confirmation
        if last_rsi > 75 and momentum < 0:  # Stronger overbought with negative momentum
            logging.info(f"RSI Scalping: Strong sell signal (RSI: {last_rsi:.2f}, Momentum: {momentum:.5f})")
            return "sell"
        elif last_rsi < 25 and momentum > 0:  # Stronger oversold with positive momentum
            logging.info(f"RSI Scalping: Strong buy signal (RSI: {last_rsi:.2f}, Momentum: {momentum:.5f})")
            return "buy"
        else:
            return "hold"
            
    except Exception as e:
        logging.error(f"Error in RSI scalping strategy: {e}")
        return "hold"

def _sma_rsi_combo_signal(df):
    """Enhanced SMA+RSI combo with additional technical filters"""
    try:
        # SMA Logic
        df['SMA10'] = df['close'].rolling(window=10).mean()
        df['SMA20'] = df['close'].rolling(window=20).mean()
        df['SMA50'] = df['close'].rolling(window=50).mean()
        
        # RSI Logic
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        
        if loss.sum() == 0:
            return "hold"
            
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # MACD for additional confirmation
        df['EMA12'] = df['close'].ewm(span=12).mean()
        df['EMA26'] = df['close'].ewm(span=26).mean()
        df['MACD'] = df['EMA12'] - df['EMA26']
        df['MACD_signal'] = df['MACD'].ewm(span=9).mean()
        df['MACD_histogram'] = df['MACD'] - df['MACD_signal']
        
        last_row = df.iloc[-1]
        prev_row = df.iloc[-2]
        
        if pd.isna(last_row['SMA10']) or pd.isna(last_row['RSI']):
            return "hold"
        
        # Trend filter using SMA50
        trend_up = last_row['close'] > last_row['SMA50']
        trend_down = last_row['close'] < last_row['SMA50']
        
        # SMA crossover signals
        sma_buy = (prev_row['SMA10'] <= prev_row['SMA20'] and 
                  last_row['SMA10'] > last_row['SMA20'])
        sma_sell = (prev_row['SMA10'] >= prev_row['SMA20'] and 
                   last_row['SMA10'] < last_row['SMA20'])
        
        # RSI conditions
        rsi_bullish = 40 < last_row['RSI'] < 70
        rsi_bearish = 30 < last_row['RSI'] < 60
        
        # MACD confirmation
        macd_bullish = last_row['MACD_histogram'] > 0
        macd_bearish = last_row['MACD_histogram'] < 0
        
        # Combined signals with multiple confirmations
        if (sma_buy and rsi_bullish and macd_bullish and trend_up):
            logging.info("SMA+RSI Combo: Strong bullish signal with trend and MACD confirmation")
            return "buy"
        elif (sma_sell and rsi_bearish and macd_bearish and trend_down):
            logging.info("SMA+RSI Combo: Strong bearish signal with trend and MACD confirmation")
            return "sell"
        else:
            return "hold"
            
    except Exception as e:
        logging.error(f"Error in SMA+RSI combo strategy: {e}")
        return "hold"

def _bollinger_bands_signal(df):
    """Bollinger Bands mean reversion strategy"""
    try:
        window = 20
        df['SMA20'] = df['close'].rolling(window=window).mean()
        df['std'] = df['close'].rolling(window=window).std()
        df['upper_band'] = df['SMA20'] + (df['std'] * 2)
        df['lower_band'] = df['SMA20'] - (df['std'] * 2)
        
        # RSI for additional confirmation
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        
        if loss.sum() == 0:
            return "hold"
            
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        last_row = df.iloc[-1]
        
        if pd.isna(last_row['upper_band']) or pd.isna(last_row['RSI']):
            return "hold"
        
        # Signal generation
        if (last_row['close'] <= last_row['lower_band'] and 
            last_row['RSI'] < 30):
            logging.info("Bollinger Bands: Oversold bounce signal")
            return "buy"
        elif (last_row['close'] >= last_row['upper_band'] and 
              last_row['RSI'] > 70):
            logging.info("Bollinger Bands: Overbought reversal signal")
            return "sell"
        else:
            return "hold"
            
    except Exception as e:
        logging.error(f"Error in Bollinger Bands strategy: {e}")
        return "hold"

def _ema_crossover_signal(df):
    """EMA crossover strategy with trend confirmation"""
    try:
        df['EMA9'] = df['close'].ewm(span=9).mean()
        df['EMA21'] = df['close'].ewm(span=21).mean()
        df['EMA50'] = df['close'].ewm(span=50).mean()
        
        last_row = df.iloc[-1]
        prev_row = df.iloc[-2]
        
        if pd.isna(last_row['EMA9']) or pd.isna(last_row['EMA21']):
            return "hold"
        
        # Trend confirmation
        trend_up = last_row['EMA21'] > last_row['EMA50']
        trend_down = last_row['EMA21'] < last_row['EMA50']
        
        # Crossover signals
        if (prev_row['EMA9'] <= prev_row['EMA21'] and 
            last_row['EMA9'] > last_row['EMA21'] and trend_up):
            logging.info("EMA Crossover: Bullish signal with trend confirmation")
            return "buy"
        elif (prev_row['EMA9'] >= prev_row['EMA21'] and 
              last_row['EMA9'] < last_row['EMA21'] and trend_down):
            logging.info("EMA Crossover: Bearish signal with trend confirmation")
            return "sell"
        else:
            return "hold"
            
    except Exception as e:
        logging.error(f"Error in EMA crossover strategy: {e}")
        return "hold"

def get_signal(df, strategy_name):
    """Router function to get a signal from the chosen strategy"""
    try:
        if strategy_name == "sma_crossover":
            return _sma_crossover_signal(df)
        elif strategy_name == "rsi_scalping":
            return _rsi_scalping_signal(df)
        elif strategy_name == "sma_rsi_combo":
            return _sma_rsi_combo_signal(df)
        elif strategy_name == "bollinger_bands":
            return _bollinger_bands_signal(df)
        elif strategy_name == "ema_crossover":
            return _ema_crossover_signal(df)
        else:
            logging.warning(f"Strategy '{strategy_name}' not found. Defaulting to 'hold'.")
            return "hold"
            
    except Exception as e:
        logging.error(f"Error in get_signal for strategy {strategy_name}: {e}")
        return "hold"

def get_available_strategies():
    """Get list of available trading strategies"""
    return [
        "sma_crossover",
        "rsi_scalping", 
        "sma_rsi_combo",
        "bollinger_bands",
        "ema_crossover"
    ]
