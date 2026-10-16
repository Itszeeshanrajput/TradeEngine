import datetime
import logging
import pytz

class PropFirmManager:
    def __init__(self, config):
        """
        config should contain prop_firm_settings from risk_management
        """
        self.settings = config.get('prop_firm_settings', {})
        self.enabled = config.get('prop_firm_mode', False)

        self.daily_drawdown_limit = self.settings.get('daily_drawdown_limit_pct', 5.0)
        self.max_total_drawdown = self.settings.get('max_total_drawdown_pct', 10.0)
        self.weekend_trading = self.settings.get('weekend_trading_allowed', False)

    def check_trading_allowed(self, account_balance, account_equity, initial_balance):
        """
        Check if trading is allowed based on prop firm rules.
        Returns (is_allowed, reason)
        """
        if not self.enabled:
            return True, "Prop firm mode disabled"

        # 1. Weekend check
        if not self.weekend_trading:
            now = datetime.datetime.now(pytz.utc)
            # Friday 21:00 UTC to Sunday 21:00 UTC
            if now.weekday() == 5 or (now.weekday() == 4 and now.hour >= 21) or (now.weekday() == 6 and now.hour < 21):
                return False, "Weekend trading is disabled per prop firm rules"

        # 2. Max Total Drawdown
        # Drawdown is calculated from the initial balance.
        # If equity drops below initial_balance * (1 - max_total_drawdown/100)
        max_loss_allowed = initial_balance * (self.max_total_drawdown / 100.0)
        current_loss = initial_balance - account_equity
        if current_loss >= max_loss_allowed:
            return False, f"Max total drawdown limit ({self.max_total_drawdown}%) reached!"

        # 3. Daily Drawdown
        # Typically prop firms calculate daily drawdown from the start of day balance or equity.
        # For simplicity, if equity drops below balance * (1 - daily_drawdown/100)
        daily_loss_allowed = account_balance * (self.daily_drawdown_limit / 100.0)
        current_daily_loss = account_balance - account_equity
        if current_daily_loss >= daily_loss_allowed:
            return False, f"Daily drawdown limit ({self.daily_drawdown_limit}%) reached!"

        return True, "Trading allowed"
