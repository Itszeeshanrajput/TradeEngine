# Gunicorn configuration file for Flask-SocketIO
bind = "0.0.0.0:5000"
worker_class = "eventlet"
workers = 1
worker_connections = 1000
timeout = 120
keepalive = 5
preload_app = True
max_requests = 1000
max_requests_jitter = 100

# Logging
loglevel = "info"
accesslog = "-"
errorlog = "-"