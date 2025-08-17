from flask import render_template, request, jsonify, redirect, url_for, flash
from app import app, db, socketio
from models import Account, Trade, BacktestResult, SystemLog
from sqlalchemy import func, desc
from datetime import datetime, timedelta
import json
import os
from backtesting import BacktestEngine
from notifications import NotificationManager

@app.route('/')
def dashboard():
    """Main dashboard view"""
    return render_template('dashboard.html')

@app.route('/analytics')
def analytics():
    """Analytics and reporting view"""
    return render_template('analytics.html')

@app.route('/backtest')
def backtest():
    """Backtesting interface"""
    return render_template('backtest.html')

@app.route('/settings')
def settings():
    """Settings and configuration view"""
    return render_template('settings.html')

@app.route('/api/accounts')
def api_accounts():
    """Get all accounts with current status"""
    accounts = Account.query.all()
    return jsonify([account.to_dict() for account in accounts])

@app.route('/api/trades')
def api_trades():
    """Get trades with optional filtering"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    status = request.args.get('status', 'all')
    symbol = request.args.get('symbol', 'all')
    
    query = Trade.query
    
    if status != 'all':
        query = query.filter(Trade.status == status.upper())
    if symbol != 'all':
        query = query.filter(Trade.symbol == symbol)
    
    trades = query.order_by(desc(Trade.open_time)).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'trades': [trade.to_dict() for trade in trades.items],
        'total': trades.total,
        'pages': trades.pages,
        'current_page': page
    })

@app.route('/api/analytics/summary')
def api_analytics_summary():
    """Get trading analytics summary"""
    # Get data for the last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    # Total trades
    total_trades = Trade.query.filter(Trade.open_time >= thirty_days_ago).count()
    
    # Winning/losing trades
    winning_trades = Trade.query.filter(
        Trade.open_time >= thirty_days_ago,
        Trade.profit > 0,
        Trade.status == 'CLOSED'
    ).count()
    
    losing_trades = Trade.query.filter(
        Trade.open_time >= thirty_days_ago,
        Trade.profit < 0,
        Trade.status == 'CLOSED'
    ).count()
    
    # Total profit/loss
    total_profit = db.session.query(func.sum(Trade.profit)).filter(
        Trade.open_time >= thirty_days_ago,
        Trade.status == 'CLOSED'
    ).scalar() or 0
    
    # Win rate
    win_rate = (winning_trades / (winning_trades + losing_trades) * 100) if (winning_trades + losing_trades) > 0 else 0
    
    # Best and worst trades
    best_trade = Trade.query.filter(
        Trade.open_time >= thirty_days_ago,
        Trade.status == 'CLOSED'
    ).order_by(desc(Trade.profit)).first()
    
    worst_trade = Trade.query.filter(
        Trade.open_time >= thirty_days_ago,
        Trade.status == 'CLOSED'
    ).order_by(Trade.profit).first()
    
    return jsonify({
        'total_trades': total_trades,
        'winning_trades': winning_trades,
        'losing_trades': losing_trades,
        'win_rate': round(win_rate, 2),
        'total_profit': round(total_profit, 2),
        'best_trade': best_trade.to_dict() if best_trade else None,
        'worst_trade': worst_trade.to_dict() if worst_trade else None
    })

@app.route('/api/analytics/daily_pnl')
def api_daily_pnl():
    """Get daily P&L data for charts"""
    days = request.args.get('days', 30, type=int)
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Query daily P&L
    daily_pnl = db.session.query(
        func.date(Trade.close_time).label('date'),
        func.sum(Trade.profit).label('profit')
    ).filter(
        Trade.close_time >= start_date,
        Trade.status == 'CLOSED'
    ).group_by(func.date(Trade.close_time)).order_by('date').all()
    
    return jsonify([{
        'date': row.date.isoformat() if row.date else None,
        'profit': float(row.profit) if row.profit else 0
    } for row in daily_pnl])

@app.route('/api/control', methods=['POST'])
def api_control():
    """Control trading bot (pause/resume)"""
    action = request.json.get('action')
    
    if action not in ['pause', 'resume']:
        return jsonify({'error': 'Invalid action'}), 400
    
    status = 'paused' if action == 'pause' else 'running'
    
    try:
        with open('control.json', 'w') as f:
            json.dump({'status': status}, f)
        
        # Emit status change to all clients
        socketio.emit('bot_status_changed', {'status': status})
        
        return jsonify({'status': status, 'message': f'Bot is now {status}'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/backtest', methods=['POST'])
def api_backtest():
    """Run a backtest"""
    data = request.json
    
    try:
        engine = BacktestEngine()
        result = engine.run_backtest(
            strategy=data['strategy'],
            symbol=data['symbol'],
            timeframe=data['timeframe'],
            start_date=datetime.fromisoformat(data['start_date']),
            end_date=datetime.fromisoformat(data['end_date']),
            initial_balance=data.get('initial_balance', 10000)
        )
        
        # Save backtest result
        backtest_result = BacktestResult(
            strategy_name=data['strategy'],
            symbol=data['symbol'],
            timeframe=data['timeframe'],
            start_date=datetime.fromisoformat(data['start_date']),
            end_date=datetime.fromisoformat(data['end_date']),
            initial_balance=data.get('initial_balance', 10000),
            final_balance=result['final_balance'],
            total_trades=result['total_trades'],
            winning_trades=result['winning_trades'],
            losing_trades=result['losing_trades'],
            max_drawdown=result['max_drawdown'],
            sharpe_ratio=result['sharpe_ratio'],
            profit_factor=result['profit_factor']
        )
        
        db.session.add(backtest_result)
        db.session.commit()
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/backtest/results')
def api_backtest_results():
    """Get backtest results"""
    results = BacktestResult.query.order_by(desc(BacktestResult.created_at)).limit(20).all()
    return jsonify([result.to_dict() for result in results])

@app.route('/api/config')
def api_config():
    """Get current configuration"""
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        return jsonify(config)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/config', methods=['POST'])
def api_config_update():
    """Update configuration"""
    try:
        config = request.json
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        flash('Configuration updated successfully', 'success')
        return jsonify({'message': 'Configuration updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/logs')
def api_logs():
    """Get system logs"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 100, type=int)
    level = request.args.get('level', 'all')
    
    query = SystemLog.query
    
    if level != 'all':
        query = query.filter(SystemLog.level == level.upper())
    
    logs = query.order_by(desc(SystemLog.timestamp)).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'logs': [log.to_dict() for log in logs.items],
        'total': logs.total,
        'pages': logs.pages,
        'current_page': page
    })

@app.route('/api/bot-control', methods=['POST'])
def api_bot_control():
    """Control bot operations"""
    try:
        data = request.get_json()
        action = data.get('action')
        
        control_data = {'status': action, 'timestamp': datetime.utcnow().isoformat()}
        
        with open('control.json', 'w') as f:
            json.dump(control_data, f)
        
        socketio.emit('bot_status_changed', {'status': action})
        
        return jsonify({'success': True, 'message': f'Bot {action}d successfully'})
    
    except Exception as e:
        logging.error(f"Error controlling bot: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/dashboard/summary')
def api_dashboard_summary():
    """Get dashboard summary data"""
    try:
        # Use database data if available, otherwise return demo data
        accounts = Account.query.filter_by(enabled=True).all()
        if not accounts:
            # Demo data for initial display
            mock_accounts = [
                {
                    'id': 1,
                    'name': 'Demo Account 1',
                    'login': 123456,
                    'server': 'Exness-Demo',
                    'balance': 10000.0,
                    'equity': 10050.0,
                    'margin': 200.0,
                    'margin_free': 9850.0,
                    'currency': 'USD',
                    'enabled': True
                }
            ]
            return jsonify({
                'accounts': mock_accounts,
                'summary': {
                    'total_balance': 10000.0,
                    'total_equity': 10050.0,
                    'open_positions': 2,
                    'today_trades': 5
                }
            })
        
        total_balance = sum(acc.balance for acc in accounts)
        total_equity = sum(acc.equity for acc in accounts)
        open_positions = Trade.query.filter_by(status='OPEN').count()
        
        today = datetime.utcnow().date()
        today_start = datetime.combine(today, datetime.min.time())
        today_trades = Trade.query.filter(Trade.open_time >= today_start).count()
        
        return jsonify({
            'accounts': [acc.to_dict() for acc in accounts],
            'summary': {
                'total_balance': total_balance,
                'total_equity': total_equity,
                'open_positions': open_positions,
                'today_trades': today_trades
            }
        })
    
    except Exception as e:
        logging.error(f"Error getting dashboard summary: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard/today-stats')  
def api_today_stats():
    """Get today's trading statistics"""
    try:
        today = datetime.utcnow().date()
        today_start = datetime.combine(today, datetime.min.time())
        
        today_trades = Trade.query.filter(Trade.open_time >= today_start).all()
        
        if not today_trades:
            # Demo data if no trades
            return jsonify({
                'total_trades': 5,
                'total_profit': 125.50,
                'winning_trades': 4,
                'win_rate': 80.0
            })
        
        total_profit = sum(trade.profit for trade in today_trades if trade.profit)
        winning_trades = len([t for t in today_trades if t.profit and t.profit > 0])
        
        return jsonify({
            'total_trades': len(today_trades),
            'total_profit': total_profit,
            'winning_trades': winning_trades,
            'win_rate': (winning_trades / len(today_trades) * 100) if today_trades else 0
        })
    
    except Exception as e:
        logging.error(f"Error getting today's stats: {e}")
        return jsonify({'error': str(e)}), 500
