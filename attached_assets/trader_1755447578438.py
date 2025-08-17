import time
import logging
import json
from datetime import datetime, time as dt_time
import MetaTrader5 as mt5

import mt5_helper
import strategy
import risk_manager

class Trader:
    def __init__(self, account_config, global_settings):
        self.config = account_config
        self.globals = global_settings
        self.name = self.config.get('name', self.config['login'])
        self.timeframe = getattr(mt5, f"TIMEFRAME_{self.globals.get('timeframe', 'M5')}")

    def _get_control_status(self):
        """Checks the control.json file for pause/resume commands."""
        try:
            with open('control.json', 'r') as f:
                return json.load(f).get('status', 'running')
        except (FileNotFoundError, json.JSONDecodeError):
            return 'running'

    def _update_dashboard_data(self):
        """Writes live account and position data to a file for the GUI."""
        acc_info = mt5.account_info()
        positions = mt5.positions_get()
        dashboard_data = {'account_info': {}, 'positions': []}
        if acc_info:
            dashboard_data['account_info'] = {
                'balance': acc_info.balance, 'equity': acc_info.equity, 'margin': acc_info.margin,
                'margin_free': acc_info.margin_free, 'currency': acc_info.currency
            }
        if positions:
            for pos in positions:
                dashboard_data['positions'].append({
                    'ticket': pos.ticket, 'symbol': pos.symbol, 'type': "BUY" if pos.type == mt5.POSITION_TYPE_BUY else "SELL",
                    'volume': pos.volume, 'price_open': pos.price_open, 'price_current': pos.price_current,
                    'sl': pos.sl, 'tp': pos.tp, 'profit': pos.profit
                })
        with open('dashboard_data.json', 'w') as f:
            json.dump(dashboard_data, f, indent=4)

    def _in_trading_session(self):
        """Checks if the current time is within the allowed trading hours."""
        if not self.globals.get("enable_time_filter", True): return True
        now = datetime.now().time()
        start = dt_time.fromisoformat(self.globals.get("trading_start", "07:00"))
        end = dt_time.fromisoformat(self.globals.get("trading_end", "17:00"))
        return start <= now <= end

    def run_session(self):
        """Connects, runs one trading cycle, and disconnects."""
        if self._get_control_status() == 'paused':
            logging.warning(f"Bot is PAUSED by user command. Skipping trading cycle for {self.name}.")
            try:
                mt5_helper.initialize_mt5(self.config['login'], self.config['password'], self.config['server'])
                self._update_dashboard_data()
                mt5_helper.shutdown_mt5()
            except Exception as e:
                 logging.error(f"[{self.name}] Failed to update dashboard while paused: {e}")
            return

        logging.info(f"--- Starting session for account: {self.name} ---")
        try:
            mt5_helper.initialize_mt5(self.config['login'], self.config['password'], self.config['server'])
        except RuntimeError as e:
            logging.error(f"[{self.name}] MT5 initialization failed: {e}")
            return

        self._update_dashboard_data()

        if not self._in_trading_session():
            logging.info(f"[{self.name}] Outside of trading session. Skipping.")
            mt5_helper.shutdown_mt5()
            return

        for symbol in self.config.get("symbols", []):
            try:
                self._process_symbol(symbol)
            except Exception as e:
                logging.error(f"[{self.name}/{symbol}] Error processing symbol: {e}", exc_info=True)
        
        mt5_helper.shutdown_mt5()
        logging.info(f"--- Session finished for account: {self.name} ---")

    def _process_symbol(self, symbol):
        """Processes a single symbol: gets data, generates a signal, and manages trades."""
        logging.info(f"[{self.name}/{symbol}] Processing...")
        
        open_positions = mt5_helper.get_open_positions(symbol)
        
        if open_positions:
            pos = open_positions[0] 
            logging.info(f"[{self.name}/{symbol}] Found open position #{pos.ticket}. Managing...")
            risk_manager.move_sl_to_breakeven(pos, symbol)
            risk_manager.update_trailing_stop(pos, symbol)

        # --- THIS IS THE CORRECTED LINE ---
        df = mt5_helper.get_data(symbol, self.timeframe, bars=100)
        
        if df is None:
            logging.warning(f"[{self.name}/{symbol}] Could not retrieve market data.")
            return

        signal = strategy.get_signal(df, self.config.get("strategy_name", "sma_crossover"))
        last_price = df['close'].iloc[-1]
        logging.info(f"[{self.name}/{symbol}] Last Price: {last_price}, Signal: {signal}")

        if not open_positions and signal in ("buy", "sell"):
            sl_pips, tp_pips = risk_manager.get_dynamic_sltp(df, symbol)
            volume = risk_manager.calculate_volume(symbol, sl_pips, self.config['risk_percent'], self.config['max_volume'])
            
            symbol_info = mt5.symbol_info(symbol)
            if not symbol_info: return

            if signal == "buy":
                sl = last_price - (sl_pips * symbol_info.point)
                tp = last_price + (tp_pips * symbol_info.point)
            else: # sell
                sl = last_price + (sl_pips * symbol_info.point)
                tp = last_price - (tp_pips * symbol_info.point)

            logging.info(f"[{self.name}/{symbol}] Placing {signal} order. Volume: {volume}, SL: {sl:.5f}, TP: {tp:.5f}")
            mt5_helper.place_order(symbol, signal, volume, sl=sl, tp=tp)