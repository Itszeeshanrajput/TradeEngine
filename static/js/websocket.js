/**
 * WebSocket Handler for Real-time Communication
 * Manages connection, reconnection, and event handling for the Forex Trading Bot
 */

class WebSocketManager {
    constructor() {
        this.socket = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;
        this.reconnectDelay = 1000;
        this.eventHandlers = {};
        this.heartbeatInterval = null;
        this.lastHeartbeat = Date.now();
        
        this.init();
    }

    init() {
        this.connect();
        this.setupHeartbeat();
        this.updateConnectionStatus('connecting');
    }

    connect() {
        try {
            // Use Socket.IO client
            this.socket = io({
                transports: ['websocket', 'polling'],
                upgrade: true,
                rememberUpgrade: true,
                timeout: 5000,
                forceNew: true
            });

            this.setupEventListeners();
            
        } catch (error) {
            console.error('WebSocket connection error:', error);
            this.handleReconnect();
        }
    }

    setupEventListeners() {
        // Connection events
        this.socket.on('connect', () => {
            console.log('WebSocket connected');
            this.isConnected = true;
            this.reconnectAttempts = 0;
            this.updateConnectionStatus('connected');
            this.lastHeartbeat = Date.now();
            
            // Subscribe to updates
            this.socket.emit('subscribe_to_updates', { type: 'all' });
            
            this.trigger('connected');
        });

        this.socket.on('disconnect', (reason) => {
            console.log('WebSocket disconnected:', reason);
            this.isConnected = false;
            this.updateConnectionStatus('disconnected');
            
            // Attempt reconnection unless it was intentional
            if (reason !== 'io client disconnect') {
                this.handleReconnect();
            }
            
            this.trigger('disconnected', { reason });
        });

        this.socket.on('connect_error', (error) => {
            console.error('WebSocket connection error:', error);
            this.updateConnectionStatus('error');
            this.handleReconnect();
        });

        // Bot status events
        this.socket.on('bot_status', (data) => {
            this.trigger('bot_status', data);
            this.updateBotStatus(data.status);
        });

        this.socket.on('bot_status_changed', (data) => {
            this.trigger('bot_status_changed', data);
            this.updateBotStatus(data.status);
            this.showNotification(`Bot status changed to: ${data.status}`, 'info');
        });

        // Trading events
        this.socket.on('trade_opened', (data) => {
            this.trigger('trade_opened', data);
            this.showTradeNotification('opened', data);
        });

        this.socket.on('trade_closed', (data) => {
            this.trigger('trade_closed', data);
            this.showTradeNotification('closed', data);
        });

        this.socket.on('new_trade', (data) => {
            this.trigger('new_trade', data);
            this.showTradeNotification('new', data);
        });

        // Account events
        this.socket.on('account_update', (data) => {
            this.trigger('account_update', data);
        });

        this.socket.on('account_updated', (data) => {
            this.trigger('account_updated', data);
        });

        // Dashboard events
        this.socket.on('dashboard_update', (data) => {
            this.trigger('dashboard_update', data);
        });

        // System events
        this.socket.on('system_log', (data) => {
            this.trigger('system_log', data);
            this.addLogEntry(data);
        });

        this.socket.on('error', (data) => {
            console.error('WebSocket error:', data);
            this.trigger('error', data);
        });

        // Subscription confirmation
        this.socket.on('subscription_confirmed', (data) => {
            console.log('Subscription confirmed:', data.type);
        });

        // Status response
        this.socket.on('status', (data) => {
            console.log('WebSocket status:', data);
        });
    }

    setupHeartbeat() {
        this.heartbeatInterval = setInterval(() => {
            if (this.isConnected) {
                // Check if we've received a heartbeat recently
                const timeSinceHeartbeat = Date.now() - this.lastHeartbeat;
                if (timeSinceHeartbeat > 30000) { // 30 seconds
                    console.warn('No heartbeat received, connection may be stale');
                    this.handleReconnect();
                }
            }
        }, 10000); // Check every 10 seconds
    }

    handleReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('Max reconnection attempts reached');
            this.updateConnectionStatus('failed');
            return;
        }

        this.reconnectAttempts++;
        this.updateConnectionStatus('reconnecting');
        
        const delay = Math.min(this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1), 30000);
        
        setTimeout(() => {
            console.log(`Reconnection attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts}`);
            this.connect();
        }, delay);
    }

    updateConnectionStatus(status) {
        const statusElement = document.getElementById('connectionStatus');
        const botStatusElement = document.getElementById('botStatus');
        
        if (statusElement) {
            const statusConfig = {
                'connecting': {
                    text: 'Connecting...',
                    class: 'text-warning',
                    icon: 'fa-spinner fa-spin'
                },
                'connected': {
                    text: 'Connected',
                    class: 'text-success',
                    icon: 'fa-circle'
                },
                'disconnected': {
                    text: 'Disconnected',
                    class: 'text-danger',
                    icon: 'fa-circle'
                },
                'reconnecting': {
                    text: 'Reconnecting...',
                    class: 'text-warning',
                    icon: 'fa-sync fa-spin'
                },
                'error': {
                    text: 'Connection Error',
                    class: 'text-danger',
                    icon: 'fa-exclamation-triangle'
                },
                'failed': {
                    text: 'Connection Failed',
                    class: 'text-danger',
                    icon: 'fa-times-circle'
                }
            };

            const config = statusConfig[status];
            if (config) {
                statusElement.className = `connection-status ${config.class}`;
                statusElement.innerHTML = `<i class="fas ${config.icon} me-1"></i>${config.text}`;
            }
        }
    }

    updateBotStatus(status) {
        const botStatusElement = document.getElementById('botStatus');
        
        if (botStatusElement) {
            const statusConfig = {
                'running': {
                    text: 'Running',
                    class: 'bg-success',
                    icon: 'fa-circle'
                },
                'paused': {
                    text: 'Paused',
                    class: 'bg-warning',
                    icon: 'fa-pause'
                },
                'stopped': {
                    text: 'Stopped',
                    class: 'bg-danger',
                    icon: 'fa-stop'
                },
                'error': {
                    text: 'Error',
                    class: 'bg-danger',
                    icon: 'fa-exclamation-triangle'
                }
            };

            const config = statusConfig[status] || statusConfig['stopped'];
            botStatusElement.className = `badge ${config.class}`;
            botStatusElement.innerHTML = `<i class="fas ${config.icon} me-1"></i>${config.text}`;
        }
    }

    showTradeNotification(type, data) {
        let title, message, variant;
        
        switch (type) {
            case 'opened':
            case 'new':
                title = 'New Trade Opened';
                message = `${data.type} ${data.volume} ${data.symbol} @ ${data.price}`;
                variant = data.type === 'BUY' ? 'success' : 'danger';
                break;
            case 'closed':
                title = 'Trade Closed';
                const profit = parseFloat(data.profit);
                message = `${data.symbol} closed with ${profit >= 0 ? 'profit' : 'loss'}: $${Math.abs(profit).toFixed(2)}`;
                variant = profit >= 0 ? 'success' : 'danger';
                break;
            default:
                return;
        }

        this.showNotification(`${title}: ${message}`, variant);
        
        // Also trigger custom event for dashboard
        this.trigger('trade_notification', { type, data, title, message, variant });
    }

    showNotification(message, type = 'info') {
        // Create toast notification
        const toastContainer = document.getElementById('liveActivityFeed') || 
                              document.querySelector('.activity-feed') ||
                              this.createNotificationContainer();

        const toast = document.createElement('div');
        toast.className = `alert alert-${type} alert-dismissible fade show activity-item`;
        toast.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="fas fa-${this.getIconForType(type)} me-2"></i>
                <div class="flex-grow-1">
                    <small class="text-muted">${new Date().toLocaleTimeString()}</small>
                    <div>${message}</div>
                </div>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="alert"></button>
            </div>
        `;

        toastContainer.appendChild(toast);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (toast.parentNode) {
                toast.remove();
            }
        }, 5000);
    }

    createNotificationContainer() {
        const container = document.createElement('div');
        container.id = 'liveActivityFeed';
        container.className = 'activity-feed';
        document.body.appendChild(container);
        return container;
    }

    getIconForType(type) {
        const icons = {
            'success': 'check-circle',
            'danger': 'exclamation-triangle',
            'warning': 'exclamation-circle',
            'info': 'info-circle',
            'primary': 'bell'
        };
        return icons[type] || 'bell';
    }

    addLogEntry(logData) {
        const logContainer = document.getElementById('tradingLog');
        if (!logContainer) return;

        const logEntry = document.createElement('div');
        logEntry.className = 'log-entry';
        
        const timestamp = new Date(logData.timestamp || Date.now()).toLocaleTimeString();
        const level = logData.level || 'INFO';
        const message = logData.message || '';
        const module = logData.module ? `[${logData.module}]` : '';

        logEntry.innerHTML = `
            <span class="log-timestamp">[${timestamp}]</span>
            <span class="log-level log-level-${level.toLowerCase()}">[${level}]</span>
            <span class="text-muted">${module}</span>
            <span class="log-message">${message}</span>
        `;

        logContainer.appendChild(logEntry);

        // Auto-scroll if user is at bottom
        const isScrolledToBottom = logContainer.scrollHeight - logContainer.clientHeight <= logContainer.scrollTop + 1;
        if (isScrolledToBottom) {
            logContainer.scrollTop = logContainer.scrollHeight;
        }

        // Limit log entries to prevent memory issues
        while (logContainer.children.length > 1000) {
            logContainer.removeChild(logContainer.firstChild);
        }
    }

    // Event handling system
    on(event, handler) {
        if (!this.eventHandlers[event]) {
            this.eventHandlers[event] = [];
        }
        this.eventHandlers[event].push(handler);
    }

    off(event, handler) {
        if (this.eventHandlers[event]) {
            const index = this.eventHandlers[event].indexOf(handler);
            if (index > -1) {
                this.eventHandlers[event].splice(index, 1);
            }
        }
    }

    trigger(event, data) {
        if (this.eventHandlers[event]) {
            this.eventHandlers[event].forEach(handler => {
                try {
                    handler(data);
                } catch (error) {
                    console.error(`Error in event handler for ${event}:`, error);
                }
            });
        }
    }

    // Public API methods
    emit(event, data) {
        if (this.socket && this.isConnected) {
            this.socket.emit(event, data);
        } else {
            console.warn('Cannot emit event, WebSocket not connected');
        }
    }

    getBotStatus() {
        if (this.socket && this.isConnected) {
            this.socket.emit('get_bot_status');
        }
    }

    controlBot(action) {
        if (this.socket && this.isConnected) {
            this.socket.emit('control_bot', { action });
        } else {
            console.warn('Cannot control bot, WebSocket not connected');
        }
    }

    disconnect() {
        if (this.socket) {
            this.socket.disconnect();
        }
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
        }
    }

    reconnect() {
        this.disconnect();
        this.reconnectAttempts = 0;
        setTimeout(() => {
            this.connect();
        }, 1000);
    }

    getConnectionStatus() {
        return {
            connected: this.isConnected,
            reconnectAttempts: this.reconnectAttempts,
            maxReconnectAttempts: this.maxReconnectAttempts
        };
    }
}

// Initialize WebSocket manager when DOM is ready
let wsManager;

document.addEventListener('DOMContentLoaded', function() {
    wsManager = new WebSocketManager();
    
    // Make it globally available
    window.wsManager = wsManager;
    
    // Setup bot control buttons
    setupBotControls();
});

function setupBotControls() {
    const pauseBtn = document.getElementById('pauseBtn');
    const resumeBtn = document.getElementById('resumeBtn');
    
    if (pauseBtn) {
        pauseBtn.addEventListener('click', function() {
            fetch('/api/control', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ action: 'pause' })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status) {
                    wsManager.showNotification(data.message, 'warning');
                }
            })
            .catch(error => {
                console.error('Error controlling bot:', error);
                wsManager.showNotification('Failed to pause bot', 'danger');
            });
        });
    }
    
    if (resumeBtn) {
        resumeBtn.addEventListener('click', function() {
            fetch('/api/control', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ action: 'resume' })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status) {
                    wsManager.showNotification(data.message, 'success');
                }
            })
            .catch(error => {
                console.error('Error controlling bot:', error);
                wsManager.showNotification('Failed to resume bot', 'danger');
            });
        });
    }
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = WebSocketManager;
}
