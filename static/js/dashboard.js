/**
 * Dashboard JavaScript
 * Main dashboard functionality for the Forex Trading Bot
 */

class DashboardManager {
    constructor() {
        this.accounts = [];
        this.trades = [];
        this.updateInterval = 30000; // 30 seconds
        this.initializeComponents();
        this.setupEventListeners();
        this.startDataUpdates();
    }

    initializeComponents() {
        // Initialize dashboard components
        this.setupMetricCards();
        this.initializeTables();
        this.setupCharts();
    }

    setupEventListeners() {
        // WebSocket event listeners
        if (window.wsManager) {
            window.wsManager.on('account_update', (data) => {
                this.updateAccountData(data);
            });

            window.wsManager.on('trade_opened', (data) => {
                this.handleNewTrade(data);
            });

            window.wsManager.on('trade_closed', (data) => {
                this.handleClosedTrade(data);
            });

            window.wsManager.on('dashboard_update', (data) => {
                this.updateDashboard(data);
            });
        }

        // Control buttons
        document.getElementById('pauseBtn')?.addEventListener('click', () => {
            this.controlBot('pause');
        });

        document.getElementById('resumeBtn')?.addEventListener('click', () => {
            this.controlBot('resume');
        });

        // Refresh button
        document.getElementById('refreshBtn')?.addEventListener('click', () => {
            this.refreshDashboard();
        });
    }

    setupMetricCards() {
        // Initialize metric cards with animation
        const metricCards = document.querySelectorAll('.metric-card');
        metricCards.forEach(card => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
            
            setTimeout(() => {
                card.style.transition = 'all 0.3s ease';
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, 100);
        });
    }

    initializeTables() {
        // Initialize DataTables if available
        if (typeof $ !== 'undefined' && $.fn.DataTable) {
            this.initializePositionsTable();
            this.initializeTradeHistoryTable();
        }
    }

    initializePositionsTable() {
        const positionsTable = $('#positionsTable');
        if (positionsTable.length) {
            this.positionsDataTable = positionsTable.DataTable({
                responsive: true,
                pageLength: 10,
                order: [[4, 'desc']], // Order by open time
                columnDefs: [
                    {
                        targets: [5, 6, 7], // P&L columns
                        className: 'text-end',
                        render: function(data, type, row) {
                            if (type === 'display') {
                                const value = parseFloat(data);
                                const className = value >= 0 ? 'text-success' : 'text-danger';
                                return `<span class="${className}">${formatCurrency(value)}</span>`;
                            }
                            return data;
                        }
                    }
                ]
            });
        }
    }

    initializeTradeHistoryTable() {
        const historyTable = $('#tradeHistoryTable');
        if (historyTable.length) {
            this.historyDataTable = historyTable.DataTable({
                responsive: true,
                pageLength: 15,
                order: [[6, 'desc']], // Order by close time
                columnDefs: [
                    {
                        targets: [4, 5], // Price columns
                        className: 'text-end'
                    },
                    {
                        targets: [7], // P&L column
                        className: 'text-end',
                        render: function(data, type, row) {
                            if (type === 'display') {
                                const value = parseFloat(data);
                                const className = value >= 0 ? 'text-success' : 'text-danger';
                                return `<span class="${className}">${formatCurrency(value)}</span>`;
                            }
                            return data;
                        }
                    }
                ]
            });
        }
    }

    setupCharts() {
        // Initialize equity curve chart
        this.setupEquityChart();
        
        // Initialize daily P&L chart
        this.setupDailyPnLChart();
    }

    setupEquityChart() {
        const canvas = document.getElementById('equityChart');
        if (!canvas || !window.ChartManager) return;

        // Mock data for initial display
        const mockData = this.generateMockEquityData();
        
        if (window.chartManager) {
            window.chartManager.createEquityChart('equityChart', mockData);
        }
    }

    setupDailyPnLChart() {
        const canvas = document.getElementById('dailyPnlChart');
        if (!canvas || !window.ChartManager) return;

        // Mock data for initial display
        const mockData = this.generateMockDailyData();
        
        if (window.chartManager) {
            window.chartManager.createDailyPnLChart('dailyPnlChart', mockData);
        }
    }

    generateMockEquityData() {
        const data = [];
        let balance = 10000;
        const today = new Date();

        for (let i = 30; i >= 0; i--) {
            const date = new Date(today);
            date.setDate(date.getDate() - i);
            
            // Add some random variation
            balance += (Math.random() - 0.5) * 200;
            
            data.push({
                date: date.toISOString(),
                balance: Math.round(balance * 100) / 100
            });
        }

        return data;
    }

    generateMockDailyData() {
        const data = [];
        const today = new Date();

        for (let i = 30; i >= 0; i--) {
            const date = new Date(today);
            date.setDate(date.getDate() - i);
            
            // Add some random P&L
            const pnl = (Math.random() - 0.5) * 400;
            
            data.push({
                date: date.toISOString(),
                profit: Math.round(pnl * 100) / 100
            });
        }

        return data;
    }

    startDataUpdates() {
        // Initial data load
        this.loadDashboardData();
        
        // Set up periodic updates
        this.updateTimer = setInterval(() => {
            this.loadDashboardData();
        }, this.updateInterval);
    }

    async loadDashboardData() {
        try {
            // Load accounts
            const accountsResponse = await fetch('/api/accounts');
            if (accountsResponse.ok) {
                this.accounts = await accountsResponse.json();
                this.updateAccountCards();
            }

            // Load recent trades
            const tradesResponse = await fetch('/api/trades?per_page=10');
            if (tradesResponse.ok) {
                const tradesData = await tradesResponse.json();
                this.trades = tradesData.trades;
                this.updateTradesTable();
            }

            // Load analytics summary
            const analyticsResponse = await fetch('/api/analytics/summary');
            if (analyticsResponse.ok) {
                const analytics = await analyticsResponse.json();
                this.updateAnalyticsCards(analytics);
            }

        } catch (error) {
            console.error('Error loading dashboard data:', error);
        }
    }

    updateAccountCards() {
        this.accounts.forEach(account => {
            this.updateAccountCard(account);
        });
    }

    updateAccountCard(account) {
        const card = document.getElementById(`account-${account.id}`);
        if (!card) return;

        // Update balance
        const balanceElement = card.querySelector('.account-balance');
        if (balanceElement) {
            balanceElement.textContent = formatCurrency(account.balance);
        }

        // Update equity
        const equityElement = card.querySelector('.account-equity');
        if (equityElement) {
            equityElement.textContent = formatCurrency(account.equity);
        }

        // Update margin
        const marginElement = card.querySelector('.account-margin');
        if (marginElement) {
            marginElement.textContent = formatCurrency(account.margin);
        }

        // Update status indicator
        const statusElement = card.querySelector('.account-status');
        if (statusElement) {
            statusElement.className = `badge ${account.enabled ? 'bg-success' : 'bg-secondary'}`;
            statusElement.textContent = account.enabled ? 'Active' : 'Inactive';
        }
    }

    updateAnalyticsCards(analytics) {
        // Total trades
        const totalTradesElement = document.getElementById('totalTrades');
        if (totalTradesElement) {
            this.animateValue(totalTradesElement, analytics.total_trades || 0);
        }

        // Win rate
        const winRateElement = document.getElementById('winRate');
        if (winRateElement) {
            const winRate = analytics.win_rate || 0;
            this.animateValue(winRateElement, winRate, '%');
        }

        // Total profit
        const totalProfitElement = document.getElementById('totalProfit');
        if (totalProfitElement) {
            const profit = analytics.total_profit || 0;
            this.animateValue(totalProfitElement, profit, '', true);
            
            // Update color based on profit/loss
            totalProfitElement.className = profit >= 0 ? 'text-success' : 'text-danger';
        }

        // Daily profit
        const dailyProfitElement = document.getElementById('dailyProfit');
        if (dailyProfitElement) {
            const dailyProfit = analytics.daily_profit || 0;
            this.animateValue(dailyProfitElement, dailyProfit, '', true);
            
            // Update color based on profit/loss
            dailyProfitElement.className = dailyProfit >= 0 ? 'text-success' : 'text-danger';
        }
    }

    animateValue(element, targetValue, suffix = '', isCurrency = false) {
        const startValue = parseFloat(element.textContent.replace(/[^0-9.-]/g, '')) || 0;
        const duration = 1000; // Animation duration in milliseconds
        const startTime = performance.now();

        const animate = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            // Easing function
            const easeOutCubic = 1 - Math.pow(1 - progress, 3);
            
            const currentValue = startValue + (targetValue - startValue) * easeOutCubic;
            
            if (isCurrency) {
                element.textContent = formatCurrency(currentValue) + suffix;
            } else {
                element.textContent = Math.round(currentValue * 100) / 100 + suffix;
            }
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };

        requestAnimationFrame(animate);
    }

    updateTradesTable() {
        // Update positions table if DataTable is initialized
        if (this.positionsDataTable) {
            // Clear and add new data
            this.positionsDataTable.clear();
            
            // Add open positions
            const openTrades = this.trades.filter(trade => trade.status === 'OPEN');
            openTrades.forEach(trade => {
                this.positionsDataTable.row.add([
                    trade.symbol,
                    `<span class="badge ${trade.trade_type === 'BUY' ? 'badge-buy' : 'badge-sell'}">${trade.trade_type}</span>`,
                    trade.volume,
                    trade.price_open,
                    new Date(trade.open_time).toLocaleString(),
                    formatCurrency(trade.profit),
                    trade.sl || '-',
                    trade.tp || '-'
                ]);
            });
            
            this.positionsDataTable.draw();
        }

        // Update trade history table
        if (this.historyDataTable) {
            // Update with recent closed trades
            const closedTrades = this.trades.filter(trade => trade.status === 'CLOSED').slice(0, 15);
            
            this.historyDataTable.clear();
            closedTrades.forEach(trade => {
                this.historyDataTable.row.add([
                    trade.symbol,
                    `<span class="badge ${trade.trade_type === 'BUY' ? 'badge-buy' : 'badge-sell'}">${trade.trade_type}</span>`,
                    trade.volume,
                    trade.strategy || '-',
                    trade.price_open,
                    trade.price_close || '-',
                    trade.close_time ? new Date(trade.close_time).toLocaleString() : '-',
                    formatCurrency(trade.profit)
                ]);
            });
            
            this.historyDataTable.draw();
        }
    }

    handleNewTrade(data) {
        // Add new trade to the list
        this.trades.unshift(data);
        
        // Update tables
        this.updateTradesTable();
        
        // Show toast notification
        this.showToast('New Trade Opened', `${data.trade_type} ${data.volume} ${data.symbol} @ ${data.price_open}`, 'success');
    }

    handleClosedTrade(data) {
        // Update trade in the list
        const tradeIndex = this.trades.findIndex(t => t.ticket === data.ticket);
        if (tradeIndex !== -1) {
            this.trades[tradeIndex] = { ...this.trades[tradeIndex], ...data };
        }
        
        // Update tables
        this.updateTradesTable();
        
        // Show toast notification
        const profit = parseFloat(data.profit);
        const profitText = profit >= 0 ? `+${formatCurrency(profit)}` : formatCurrency(profit);
        this.showToast('Trade Closed', `${data.symbol} closed with ${profitText}`, profit >= 0 ? 'success' : 'danger');
    }

    updateAccountData(data) {
        // Update account in the list
        const accountIndex = this.accounts.findIndex(a => a.id === data.id);
        if (accountIndex !== -1) {
            this.accounts[accountIndex] = { ...this.accounts[accountIndex], ...data };
            this.updateAccountCard(this.accounts[accountIndex]);
        }
    }

    updateDashboard(data) {
        // Handle general dashboard updates
        if (data.accounts) {
            this.accounts = data.accounts;
            this.updateAccountCards();
        }
        
        if (data.analytics) {
            this.updateAnalyticsCards(data.analytics);
        }
    }

    controlBot(action) {
        fetch('/api/control', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ action })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.showToast('Bot Control', data.message, 'success');
            } else {
                this.showToast('Error', data.message || 'Failed to control bot', 'danger');
            }
        })
        .catch(error => {
            console.error('Error controlling bot:', error);
            this.showToast('Error', 'Failed to control bot', 'danger');
        });
    }

    refreshDashboard() {
        // Clear existing data
        this.accounts = [];
        this.trades = [];
        
        // Reload data
        this.loadDashboardData();
        
        // Show feedback
        this.showToast('Dashboard', 'Dashboard refreshed', 'info');
    }

    showToast(title, message, type = 'info') {
        // Create toast notification
        const toastContainer = document.getElementById('toastContainer') || this.createToastContainer();
        
        const toastId = 'toast-' + Date.now();
        const toast = document.createElement('div');
        toast.id = toastId;
        toast.className = `toast align-items-center text-white bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    <strong>${title}</strong><br>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;

        toastContainer.appendChild(toast);

        // Show toast using Bootstrap
        if (typeof bootstrap !== 'undefined') {
            const bsToast = new bootstrap.Toast(toast);
            bsToast.show();
            
            // Remove toast after it's hidden
            toast.addEventListener('hidden.bs.toast', () => {
                toast.remove();
            });
        } else {
            // Fallback: remove after 5 seconds
            setTimeout(() => {
                toast.remove();
            }, 5000);
        }
    }

    createToastContainer() {
        const container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '1055';
        document.body.appendChild(container);
        return container;
    }

    destroy() {
        // Cleanup
        if (this.updateTimer) {
            clearInterval(this.updateTimer);
        }
        
        if (this.positionsDataTable) {
            this.positionsDataTable.destroy();
        }
        
        if (this.historyDataTable) {
            this.historyDataTable.destroy();
        }
    }
}

// Utility functions
function formatCurrency(value, currency = 'USD') {
    if (typeof value !== 'number') {
        value = parseFloat(value) || 0;
    }
    
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currency,
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(value);
}

function formatPercentage(value) {
    if (typeof value !== 'number') {
        value = parseFloat(value) || 0;
    }
    
    return value.toFixed(2) + '%';
}

function formatVolume(value) {
    if (typeof value !== 'number') {
        value = parseFloat(value) || 0;
    }
    
    return value.toFixed(2);
}

// Initialize dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Wait for WebSocket manager to be ready
    setTimeout(() => {
        window.dashboardManager = new DashboardManager();
    }, 100);
});

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    if (window.dashboardManager) {
        window.dashboardManager.destroy();
    }
});