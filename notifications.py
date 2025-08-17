import smtplib
import requests
import logging
import os

try:
    from email.mime.text import MimeText
    from email.mime.multipart import MimeMultipart
    EMAIL_IMPORTS_AVAILABLE = True
except ImportError:
    EMAIL_IMPORTS_AVAILABLE = False

class NotificationManager:
    def __init__(self):
        self.email_enabled = self._check_email_config()
        self.sms_enabled = self._check_sms_config()
    
    def _check_email_config(self):
        """Check if email configuration is available"""
        if not EMAIL_IMPORTS_AVAILABLE:
            return False
        required_vars = ['SMTP_SERVER', 'SMTP_PORT', 'EMAIL_USER', 'EMAIL_PASSWORD', 'NOTIFICATION_EMAIL']
        return all(os.getenv(var) for var in required_vars)
    
    def _check_sms_config(self):
        """Check if SMS configuration is available"""
        return bool(os.getenv('TWILIO_SID') and os.getenv('TWILIO_TOKEN') and os.getenv('NOTIFICATION_PHONE'))
    
    def send_trade_notification(self, trade_info):
        """Send notification for new trades"""
        subject = f"New Trade Opened: {trade_info['symbol']}"
        message = f"""
        New trade has been opened:
        
        Symbol: {trade_info['symbol']}
        Type: {trade_info['type']}
        Volume: {trade_info['volume']}
        Entry Price: {trade_info['price']}
        Stop Loss: {trade_info['sl']}
        Take Profit: {trade_info['tp']}
        Strategy: {trade_info['strategy']}
        Account: {trade_info['account']}
        """
        
        self._send_notifications(subject, message)
    
    def send_trade_closed_notification(self, trade_info):
        """Send notification when trades are closed"""
        profit_loss = "Profit" if trade_info['profit'] > 0 else "Loss"
        subject = f"Trade Closed - {profit_loss}: {trade_info['symbol']}"
        
        message = f"""
        Trade has been closed:
        
        Symbol: {trade_info['symbol']}
        Type: {trade_info['type']}
        Volume: {trade_info['volume']}
        Entry Price: {trade_info['price_open']}
        Exit Price: {trade_info['price_close']}
        Profit/Loss: ${trade_info['profit']:.2f}
        Duration: {trade_info['duration']}
        Account: {trade_info['account']}
        """
        
        self._send_notifications(subject, message)
    
    def send_error_notification(self, error_message):
        """Send notification for critical errors"""
        subject = "Forex Bot - Critical Error"
        message = f"A critical error occurred in the trading bot:\n\n{error_message}"
        
        self._send_notifications(subject, message)
    
    def send_daily_summary(self, summary_data):
        """Send daily trading summary"""
        subject = "Forex Bot - Daily Trading Summary"
        message = f"""
        Daily Trading Summary:
        
        Total Trades: {summary_data['total_trades']}
        Winning Trades: {summary_data['winning_trades']}
        Losing Trades: {summary_data['losing_trades']}
        Win Rate: {summary_data['win_rate']:.2f}%
        Total P&L: ${summary_data['total_pnl']:.2f}
        Best Trade: ${summary_data['best_trade']:.2f}
        Worst Trade: ${summary_data['worst_trade']:.2f}
        
        Account Balances:
        """
        
        for account in summary_data['accounts']:
            message += f"- {account['name']}: ${account['balance']:.2f}\n"
        
        self._send_notifications(subject, message)
    
    def _send_notifications(self, subject, message):
        """Send both email and SMS notifications"""
        if self.email_enabled:
            self._send_email(subject, message)
        
        if self.sms_enabled:
            self._send_sms(f"{subject}: {message[:100]}...")
    
    def _send_email(self, subject, message):
        """Send email notification"""
        if not EMAIL_IMPORTS_AVAILABLE:
            logging.warning("Email functionality unavailable - missing email modules")
            return
            
        try:
            smtp_server = os.getenv('SMTP_SERVER')
            smtp_port = int(os.getenv('SMTP_PORT', 587))
            email_user = os.getenv('EMAIL_USER')
            email_password = os.getenv('EMAIL_PASSWORD')
            to_email = os.getenv('NOTIFICATION_EMAIL')
            
            msg = MimeMultipart()
            msg['From'] = email_user
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MimeText(message, 'plain'))
            
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(email_user, email_password)
            server.send_message(msg)
            server.quit()
            
            logging.info(f"Email notification sent: {subject}")
            
        except Exception as e:
            logging.error(f"Failed to send email notification: {e}")
    
    def _send_sms(self, message):
        """Send SMS notification using Twilio"""
        try:
            from twilio.rest import Client
            
            account_sid = os.getenv('TWILIO_SID')
            auth_token = os.getenv('TWILIO_TOKEN')
            from_phone = os.getenv('TWILIO_PHONE')
            to_phone = os.getenv('NOTIFICATION_PHONE')
            
            client = Client(account_sid, auth_token)
            
            message = client.messages.create(
                body=message[:160],  # SMS limit
                from_=from_phone,
                to=to_phone
            )
            
            logging.info(f"SMS notification sent: {message.sid}")
            
        except ImportError:
            logging.warning("Twilio library not installed. SMS notifications disabled.")
        except Exception as e:
            logging.error(f"Failed to send SMS notification: {e}")
