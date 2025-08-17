import pandas as pd
import logging

def _sma_crossover_signal(df):
    """Generates a signal based on a 10/20 SMA crossover."""
    df['SMA10'] = df['close'].rolling(window=10).mean()
    df['SMA20'] = df['close'].rolling(window=20).mean()

    last_row = df.iloc[-1]
    prev_row = df.iloc[-2]

    if pd.isna(last_row['SMA10']) or pd.isna(last_row['SMA20']):
        return "hold"
    
    if prev_row['SMA10'] <= prev_row['SMA20'] and last_row['SMA10'] > last_row['SMA20']:
        return "buy"
    elif prev_row['SMA10'] >= prev_row['SMA20'] and last_row['SMA10'] < last_row['SMA20']:
        return "sell"
    else:
        return "hold"

def _rsi_scalping_signal(df):
    """Generates a scalping signal based on RSI overbought/oversold levels."""
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    if loss.sum() == 0: return "hold" # Avoid division by zero
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    last_rsi = df['RSI'].iloc[-1]

    if pd.isna(last_rsi):
        return "hold"
    
    if last_rsi > 70:
        return "sell"
    elif last_rsi < 30:
        return "buy"
    else:
        return "hold"

def _sma_rsi_combo_signal(df):
    """
    NEW: Generates a signal only if both SMA Crossover and RSI agree.
    This provides stronger confirmation.
    """
    # 1. SMA Logic
    df['SMA10'] = df['close'].rolling(window=10).mean()
    df['SMA20'] = df['close'].rolling(window=20).mean()
    last_row = df.iloc[-1]
    prev_row = df.iloc[-2]
    sma_buy = prev_row['SMA10'] <= prev_row['SMA20'] and last_row['SMA10'] > last_row['SMA20']
    sma_sell = prev_row['SMA10'] >= prev_row['SMA20'] and last_row['SMA10'] < last_row['SMA20']
    
    # 2. RSI Logic
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    if loss.sum() == 0: return "hold"
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    last_rsi = df['RSI'].iloc[-1]

    if pd.isna(last_rsi) or pd.isna(last_row['SMA10']):
        return "hold"

    # 3. Confluence Logic: Both must agree
    if sma_buy and last_rsi > 50:
        logging.info("Signal justification: SMA bullish crossover and RSI > 50.")
        return "buy"
    elif sma_sell and last_rsi < 50:
        logging.info("Signal justification: SMA bearish crossover and RSI < 50.")
        return "sell"
    else:
        return "hold"

def get_signal(df, strategy_name):
    """Router function to get a signal from the chosen strategy."""
    if strategy_name == "sma_crossover":
        return _sma_crossover_signal(df)
    elif strategy_name == "rsi_scalping":
        return _rsi_scalping_signal(df)
    elif strategy_name == "sma_rsi_combo":
        return _sma_rsi_combo_signal(df)
    else:
        logging.warning(f"Strategy '{strategy_name}' not found. Defaulting to 'hold'.")
        return "hold"