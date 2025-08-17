import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    
try:
    from strategy import get_signal
    from risk_manager import get_dynamic_sltp
except ImportError:
    # Mock functions for development
    def get_signal(data, strategy):
        return None
    
    def get_dynamic_sltp(symbol, entry_price, trade_type, balance):
        return None, None

class BacktestEngine:
    def __init__(self):
        self.trades = []
        self.balance_history = []
        self.drawdowns = []
    
    def run_backtest(self, strategy, symbol, timeframe, start_date, end_date, initial_balance=10000):
        """Run a comprehensive backtest"""
        self.trades = []
        self.balance_history = []
        self.drawdowns = []
        
        # Initialize MT5 for data retrieval
        if not MT5_AVAILABLE:
            raise RuntimeError("MetaTrader5 not available for backtesting")
        
        if not mt5.initialize():
            raise RuntimeError("Failed to initialize MT5 for backtesting")
        
        try:
            # Get historical data
            timeframe_mt5 = getattr(mt5, f"TIMEFRAME_{timeframe}")
            
            # Calculate number of bars needed
            days_diff = (end_date - start_date).days
            bars_needed = max(1000, days_diff * 48)  # Estimate bars per day
            
            rates = mt5.copy_rates_range(symbol, timeframe_mt5, start_date, end_date)
            
            if rates is None or len(rates) == 0:
                raise ValueError(f"No historical data available for {symbol}")
            
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            
            # Run the backtest
            result = self._simulate_trades(df, strategy, symbol, initial_balance)
            
            return result
            
        finally:
            mt5.shutdown()
    
    def _simulate_trades(self, df, strategy, symbol, initial_balance):
        """Simulate trading with the given strategy"""
        balance = initial_balance
        equity = initial_balance
        peak_balance = initial_balance
        max_drawdown = 0
        open_trades = []
        
        self.balance_history.append({'time': df.iloc[0]['time'], 'balance': balance})
        
        for i in range(50, len(df)):  # Start after enough data for indicators
            current_data = df.iloc[:i+1]
            current_bar = df.iloc[i]
            
            # Get trading signal
            signal = get_signal(current_data, strategy)
            
            # Close existing trades if conditions are met
            for trade in open_trades[:]:  # Use slice copy to modify list during iteration
                trade_result = self._check_trade_exit(trade, current_bar, current_data)
                if trade_result:
                    balance += trade_result['profit']
                    equity = balance
                    
                    trade_result['close_time'] = current_bar['time']
                    trade_result['balance_after'] = balance
                    self.trades.append(trade_result)
                    open_trades.remove(trade)
            
            # Open new trade if signal and no existing trades
            if signal in ['buy', 'sell'] and len(open_trades) == 0:
                trade = self._open_trade(signal, current_bar, current_data, symbol, balance)
                if trade:
                    open_trades.append(trade)
            
            # Update balance history and drawdown
            self.balance_history.append({'time': current_bar['time'], 'balance': balance})
            
            if balance > peak_balance:
                peak_balance = balance
            
            current_drawdown = (peak_balance - balance) / peak_balance * 100
            if current_drawdown > max_drawdown:
                max_drawdown = current_drawdown
        
        # Close any remaining open trades
        for trade in open_trades:
            final_bar = df.iloc[-1]
            trade_result = self._force_close_trade(trade, final_bar)
            balance += trade_result['profit']
            self.trades.append(trade_result)
        
        # Calculate performance metrics
        return self._calculate_metrics(initial_balance, balance, max_drawdown)
    
    def _open_trade(self, signal, bar, data, symbol, balance):
        """Open a new trade"""
        # Get dynamic SL/TP
        sl_pips, tp_pips = get_dynamic_sltp(data, symbol)
        
        # Simulate position sizing (1% risk)
        risk_percent = 1.0
        risk_amount = balance * (risk_percent / 100)
        
        # Estimate point value (simplified)
        point = 0.0001 if 'JPY' not in symbol else 0.01
        if 'XAU' in symbol or 'GOLD' in symbol:
            point = 0.01
        
        # Calculate volume based on risk
        sl_in_price = sl_pips * point
        volume = min(0.1, risk_amount / (sl_in_price * 100000))  # Simplified calculation
        
        entry_price = bar['close']
        
        if signal == 'buy':
            sl_price = entry_price - (sl_pips * point)
            tp_price = entry_price + (tp_pips * point)
        else:  # sell
            sl_price = entry_price + (sl_pips * point)
            tp_price = entry_price - (tp_pips * point)
        
        trade = {
            'type': signal,
            'entry_price': entry_price,
            'sl': sl_price,
            'tp': tp_price,
            'volume': volume,
            'open_time': bar['time'],
            'symbol': symbol,
            'point': point
        }
        
        return trade
    
    def _check_trade_exit(self, trade, bar, data):
        """Check if trade should be closed"""
        current_price = bar['close']
        
        # Check SL/TP
        if trade['type'] == 'buy':
            if current_price <= trade['sl'] or current_price >= trade['tp']:
                exit_price = trade['sl'] if current_price <= trade['sl'] else trade['tp']
                profit = (exit_price - trade['entry_price']) * trade['volume'] * 100000
                return {
                    'type': trade['type'],
                    'entry_price': trade['entry_price'],
                    'exit_price': exit_price,
                    'profit': profit,
                    'volume': trade['volume'],
                    'symbol': trade['symbol'],
                    'open_time': trade['open_time'],
                    'exit_reason': 'SL' if current_price <= trade['sl'] else 'TP'
                }
        else:  # sell
            if current_price >= trade['sl'] or current_price <= trade['tp']:
                exit_price = trade['sl'] if current_price >= trade['sl'] else trade['tp']
                profit = (trade['entry_price'] - exit_price) * trade['volume'] * 100000
                return {
                    'type': trade['type'],
                    'entry_price': trade['entry_price'],
                    'exit_price': exit_price,
                    'profit': profit,
                    'volume': trade['volume'],
                    'symbol': trade['symbol'],
                    'open_time': trade['open_time'],
                    'exit_reason': 'SL' if current_price >= trade['sl'] else 'TP'
                }
        
        return None
    
    def _force_close_trade(self, trade, bar):
        """Force close trade at the end of backtest"""
        exit_price = bar['close']
        
        if trade['type'] == 'buy':
            profit = (exit_price - trade['entry_price']) * trade['volume'] * 100000
        else:
            profit = (trade['entry_price'] - exit_price) * trade['volume'] * 100000
        
        return {
            'type': trade['type'],
            'entry_price': trade['entry_price'],
            'exit_price': exit_price,
            'profit': profit,
            'volume': trade['volume'],
            'symbol': trade['symbol'],
            'open_time': trade['open_time'],
            'close_time': bar['time'],
            'exit_reason': 'End of backtest'
        }
    
    def _calculate_metrics(self, initial_balance, final_balance, max_drawdown):
        """Calculate comprehensive performance metrics"""
        if not self.trades:
            return {
                'initial_balance': initial_balance,
                'final_balance': final_balance,
                'total_return': 0,
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'max_drawdown': max_drawdown,
                'profit_factor': 0,
                'sharpe_ratio': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'trades': []
            }
        
        total_trades = len(self.trades)
        winning_trades = len([t for t in self.trades if t['profit'] > 0])
        losing_trades = len([t for t in self.trades if t['profit'] < 0])
        
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        # Calculate profit factor
        gross_profit = sum([t['profit'] for t in self.trades if t['profit'] > 0])
        gross_loss = abs(sum([t['profit'] for t in self.trades if t['profit'] < 0]))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Calculate average win/loss
        avg_win = gross_profit / winning_trades if winning_trades > 0 else 0
        avg_loss = gross_loss / losing_trades if losing_trades > 0 else 0
        
        # Calculate Sharpe ratio (simplified)
        returns = []
        for i in range(1, len(self.balance_history)):
            prev_balance = self.balance_history[i-1]['balance']
            curr_balance = self.balance_history[i]['balance']
            daily_return = (curr_balance - prev_balance) / prev_balance
            returns.append(daily_return)
        
        if returns:
            avg_return = np.mean(returns)
            std_return = np.std(returns)
            sharpe_ratio = (avg_return / std_return * np.sqrt(252)) if std_return > 0 else 0
        else:
            sharpe_ratio = 0
        
        total_return = ((final_balance - initial_balance) / initial_balance * 100)
        
        return {
            'initial_balance': initial_balance,
            'final_balance': final_balance,
            'total_return': round(total_return, 2),
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': round(win_rate, 2),
            'max_drawdown': round(max_drawdown, 2),
            'profit_factor': round(profit_factor, 2),
            'sharpe_ratio': round(sharpe_ratio, 2),
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2),
            'gross_profit': round(gross_profit, 2),
            'gross_loss': round(gross_loss, 2),
            'trades': self.trades,
            'balance_history': self.balance_history
        }
