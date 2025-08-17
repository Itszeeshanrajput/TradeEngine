from datetime import datetime
from app import db
from sqlalchemy import func

class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    login = db.Column(db.Integer, nullable=False)
    server = db.Column(db.String(100), nullable=False)
    balance = db.Column(db.Float, default=0.0)
    equity = db.Column(db.Float, default=0.0)
    margin = db.Column(db.Float, default=0.0)
    margin_free = db.Column(db.Float, default=0.0)
    currency = db.Column(db.String(10), default='USD')
    enabled = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    trades = db.relationship('Trade', backref='account', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'login': self.login,
            'server': self.server,
            'balance': self.balance,
            'equity': self.equity,
            'margin': self.margin,
            'margin_free': self.margin_free,
            'currency': self.currency,
            'enabled': self.enabled
        }

class Trade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    ticket = db.Column(db.BigInteger, nullable=False)
    symbol = db.Column(db.String(20), nullable=False)
    trade_type = db.Column(db.String(10), nullable=False)  # BUY/SELL
    volume = db.Column(db.Float, nullable=False)
    price_open = db.Column(db.Float, nullable=False)
    price_close = db.Column(db.Float)
    sl = db.Column(db.Float)
    tp = db.Column(db.Float)
    profit = db.Column(db.Float, default=0.0)
    commission = db.Column(db.Float, default=0.0)
    swap = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='OPEN')  # OPEN/CLOSED
    strategy = db.Column(db.String(50))
    open_time = db.Column(db.DateTime, default=datetime.utcnow)
    close_time = db.Column(db.DateTime)
    comment = db.Column(db.String(200))
    
    def to_dict(self):
        return {
            'id': self.id,
            'ticket': self.ticket,
            'symbol': self.symbol,
            'trade_type': self.trade_type,
            'volume': self.volume,
            'price_open': self.price_open,
            'price_close': self.price_close,
            'sl': self.sl,
            'tp': self.tp,
            'profit': self.profit,
            'commission': self.commission,
            'swap': self.swap,
            'status': self.status,
            'strategy': self.strategy,
            'open_time': self.open_time.isoformat() if self.open_time else None,
            'close_time': self.close_time.isoformat() if self.close_time else None,
            'comment': self.comment
        }

class BacktestResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    strategy_name = db.Column(db.String(50), nullable=False)
    symbol = db.Column(db.String(20), nullable=False)
    timeframe = db.Column(db.String(10), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    initial_balance = db.Column(db.Float, nullable=False)
    final_balance = db.Column(db.Float, nullable=False)
    total_trades = db.Column(db.Integer, default=0)
    winning_trades = db.Column(db.Integer, default=0)
    losing_trades = db.Column(db.Integer, default=0)
    max_drawdown = db.Column(db.Float, default=0.0)
    sharpe_ratio = db.Column(db.Float, default=0.0)
    profit_factor = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'strategy_name': self.strategy_name,
            'symbol': self.symbol,
            'timeframe': self.timeframe,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'initial_balance': self.initial_balance,
            'final_balance': self.final_balance,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'max_drawdown': self.max_drawdown,
            'sharpe_ratio': self.sharpe_ratio,
            'profit_factor': self.profit_factor,
            'return_pct': ((self.final_balance - self.initial_balance) / self.initial_balance * 100) if self.initial_balance > 0 else 0
        }

class SystemLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    level = db.Column(db.String(20), nullable=False)
    message = db.Column(db.Text, nullable=False)
    module = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'level': self.level,
            'message': self.message,
            'module': self.module,
            'timestamp': self.timestamp.isoformat()
        }
