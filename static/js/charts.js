/**
 * Charts Utilities
 * Provides chart configuration, creation, and management utilities
 * for the Forex Trading Bot dashboard
 */

// Default Chart.js configuration
const defaultChartConfig = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
        intersect: false,
        mode: 'index'
    },
    plugins: {
        legend: {
            labels: {
                usePointStyle: true,
                padding: 20,
                color: 'rgba(255, 255, 255, 0.8)'
            }
        },
        tooltip: {
            backgroundColor: 'rgba(17, 24, 39, 0.95)',
            titleColor: 'rgba(255, 255, 255, 0.9)',
            bodyColor: 'rgba(255, 255, 255, 0.8)',
            borderColor: 'rgba(75, 85, 99, 0.3)',
            borderWidth: 1,
            cornerRadius: 8,
            displayColors: true,
            callbacks: {
                label: function(context) {
                    const label = context.dataset.label || '';
                    const value = context.parsed.y;
                    
                    if (label.includes('P&L') || label.includes('Profit') || label.includes('Balance')) {
                        return `${label}: ${formatCurrency(value)}`;
                    }
                    
                    return `${label}: ${value}`;
                }
            }
        }
    },
    scales: {
        x: {
            grid: {
                color: 'rgba(75, 85, 99, 0.2)',
                drawBorder: false
            },
            ticks: {
                color: 'rgba(255, 255, 255, 0.7)'
            }
        },
        y: {
            grid: {
                color: 'rgba(75, 85, 99, 0.2)',
                drawBorder: false
            },
            ticks: {
                color: 'rgba(255, 255, 255, 0.7)',
                callback: function(value) {
                    // Format currency values
                    if (this.options.scales.y.currency) {
                        return formatCurrency(value);
                    }
                    return value;
                }
            }
        }
    }
};

// Color scheme for charts
const chartColors = {
    primary: 'rgb(59, 130, 246)',
    success: 'rgb(16, 185, 129)',
    danger: 'rgb(239, 68, 68)',
    warning: 'rgb(245, 158, 11)',
    info: 'rgb(14, 165, 233)',
    gray: 'rgb(107, 114, 128)',
    
    // Gradient colors
    gradients: {
        green: ['rgba(16, 185, 129, 0.8)', 'rgba(16, 185, 129, 0.1)'],
        red: ['rgba(239, 68, 68, 0.8)', 'rgba(239, 68, 68, 0.1)'],
        blue: ['rgba(59, 130, 246, 0.8)', 'rgba(59, 130, 246, 0.1)'],
        yellow: ['rgba(245, 158, 11, 0.8)', 'rgba(245, 158, 11, 0.1)']
    }
};

class ChartManager {
    constructor() {
        this.charts = new Map();
        this.gradients = new Map();
        
        // Set global Chart.js defaults for dark theme
        this.setupChartDefaults();
    }

    setupChartDefaults() {
        Chart.defaults.color = 'rgba(255, 255, 255, 0.8)';
        Chart.defaults.backgroundColor = 'rgba(255, 255, 255, 0.1)';
        Chart.defaults.borderColor = 'rgba(255, 255, 255, 0.2)';
        Chart.defaults.font.family = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
    }

    createGradient(ctx, color1, color2, direction = 'vertical') {
        const gradient = direction === 'vertical' 
            ? ctx.createLinearGradient(0, 0, 0, ctx.canvas.height)
            : ctx.createLinearGradient(0, 0, ctx.canvas.width, 0);
            
        gradient.addColorStop(0, color1);
        gradient.addColorStop(1, color2);
        
        return gradient;
    }

    // Equity curve chart
    createEquityChart(canvasId, data, options = {}) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) {
            console.error(`Canvas with id '${canvasId}' not found`);
            return null;
        }

        // Destroy existing chart
        this.destroyChart(canvasId);

        // Prepare data
        const chartData = {
            labels: data.map(item => new Date(item.date)),
            datasets: [{
                label: 'Account Equity',
                data: data.map(item => item.balance || item.equity || item.value),
                borderColor: chartColors.success,
                backgroundColor: this.createGradient(ctx.getContext('2d'), ...chartColors.gradients.green),
                borderWidth: 2,
                fill: true,
                tension: 0.3,
                pointRadius: 0,
                pointHoverRadius: 6,
                pointHoverBackgroundColor: chartColors.success,
                pointHoverBorderColor: '#ffffff',
                pointHoverBorderWidth: 2
            }]
        };

        const config = this.mergeConfig({
            type: 'line',
            data: chartData,
            options: {
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            unit: 'day',
                            displayFormats: {
                                day: 'MMM dd'
                            }
                        },
                        title: {
                            display: true,
                            text: 'Date'
                        }
                    },
                    y: {
                        currency: true,
                        title: {
                            display: true,
                            text: 'Account Value'
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        }, options);

        const chart = new Chart(ctx, config);
        this.charts.set(canvasId, chart);
        
        return chart;
    }

    // Daily P&L chart
    createDailyPnLChart(canvasId, data, options = {}) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        this.destroyChart(canvasId);

        const chartData = {
            labels: data.map(item => new Date(item.date)),
            datasets: [{
                label: 'Daily P&L',
                data: data.map(item => item.profit || item.pnl || 0),
                backgroundColor: data.map(item => {
                    const value = item.profit || item.pnl || 0;
                    return value >= 0 ? chartColors.success : chartColors.danger;
                }),
                borderColor: data.map(item => {
                    const value = item.profit || item.pnl || 0;
                    return value >= 0 ? chartColors.success : chartColors.danger;
                }),
                borderWidth: 1
            }]
        };

        const config = this.mergeConfig({
            type: 'bar',
            data: chartData,
            options: {
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            unit: 'day',
                            displayFormats: {
                                day: 'MMM dd'
                            }
                        }
                    },
                    y: {
                        currency: true,
                        title: {
                            display: true,
                            text: 'Profit/Loss'
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        }, options);

        const chart = new Chart(ctx, config);
        this.charts.set(canvasId, chart);
        
        return chart;
    }

    // Strategy performance chart
    createStrategyChart(canvasId, strategies, options = {}) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        this.destroyChart(canvasId);

        const chartData = {
            labels: strategies.map(s => s.name),
            datasets: [{
                label: 'Profit/Loss',
                data: strategies.map(s => s.profit || 0),
                backgroundColor: strategies.map(s => {
                    const profit = s.profit || 0;
                    return profit >= 0 ? chartColors.success : chartColors.danger;
                }),
                borderColor: strategies.map(s => {
                    const profit = s.profit || 0;
                    return profit >= 0 ? chartColors.success : chartColors.danger;
                }),
                borderWidth: 1
            }]
        };

        const config = this.mergeConfig({
            type: 'bar',
            data: chartData,
            options: {
                indexAxis: 'y',
                scales: {
                    x: {
                        currency: true,
                        title: {
                            display: true,
                            text: 'Profit/Loss'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Strategy'
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        }, options);

        const chart = new Chart(ctx, config);
        this.charts.set(canvasId, chart);
        
        return chart;
    }

    // Symbol performance chart
    createSymbolChart(canvasId, symbols, options = {}) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        this.destroyChart(canvasId);

        const chartData = {
            labels: symbols.map(s => s.symbol),
            datasets: [{
                label: 'Profit/Loss',
                data: symbols.map(s => s.profit || 0),
                backgroundColor: symbols.map(s => {
                    const profit = s.profit || 0;
                    return profit >= 0 ? chartColors.success : chartColors.danger;
                }),
                borderColor: symbols.map(s => {
                    const profit = s.profit || 0;
                    return profit >= 0 ? chartColors.success : chartColors.danger;
                }),
                borderWidth: 1
            }]
        };

        const config = this.mergeConfig({
            type: 'bar',
            data: chartData,
            options: {
                indexAxis: 'y',
                scales: {
                    x: {
                        currency: true
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        }, options);

        const chart = new Chart(ctx, config);
        this.charts.set(canvasId, chart);
        
        return chart;
    }

    // Drawdown chart
    createDrawdownChart(canvasId, data, options = {}) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        this.destroyChart(canvasId);

        // Calculate drawdown from equity data
        let peak = 0;
        const drawdownData = data.map(item => {
            const value = item.balance || item.equity || item.value || 0;
            if (value > peak) peak = value;
            const drawdown = peak > 0 ? ((peak - value) / peak) * 100 : 0;
            return {
                date: item.date,
                drawdown: -drawdown // Negative for visual representation
            };
        });

        const chartData = {
            labels: drawdownData.map(item => new Date(item.date)),
            datasets: [{
                label: 'Drawdown %',
                data: drawdownData.map(item => item.drawdown),
                borderColor: chartColors.danger,
                backgroundColor: this.createGradient(ctx.getContext('2d'), ...chartColors.gradients.red),
                borderWidth: 2,
                fill: true,
                tension: 0.3,
                pointRadius: 0,
                pointHoverRadius: 6
            }]
        };

        const config = this.mergeConfig({
            type: 'line',
            data: chartData,
            options: {
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            unit: 'day'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Drawdown %'
                        },
                        ticks: {
                            callback: function(value) {
                                return value.toFixed(1) + '%';
                            }
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        }, options);

        const chart = new Chart(ctx, config);
        this.charts.set(canvasId, chart);
        
        return chart;
    }

    // Pie chart for trade distribution
    createTradeDistributionChart(canvasId, data, options = {}) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        this.destroyChart(canvasId);

        const chartData = {
            labels: ['Winning Trades', 'Losing Trades', 'Breakeven Trades'],
            datasets: [{
                data: [
                    data.winning_trades || 0,
                    data.losing_trades || 0,
                    data.breakeven_trades || 0
                ],
                backgroundColor: [
                    chartColors.success,
                    chartColors.danger,
                    chartColors.gray
                ],
                borderWidth: 2,
                borderColor: '#1f2937'
            }]
        };

        const config = this.mergeConfig({
            type: 'doughnut',
            data: chartData,
            options: {
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            usePointStyle: true
                        }
                    }
                },
                cutout: '60%'
            }
        }, options);

        const chart = new Chart(ctx, config);
        this.charts.set(canvasId, chart);
        
        return chart;
    }

    // Monthly returns heatmap (simplified version using bars)
    createMonthlyReturnsChart(canvasId, data, options = {}) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        this.destroyChart(canvasId);

        // Group data by month
        const monthlyData = this.groupDataByMonth(data);

        const chartData = {
            labels: Object.keys(monthlyData),
            datasets: [{
                label: 'Monthly Return %',
                data: Object.values(monthlyData),
                backgroundColor: Object.values(monthlyData).map(value => 
                    value >= 0 ? chartColors.success : chartColors.danger
                ),
                borderColor: Object.values(monthlyData).map(value => 
                    value >= 0 ? chartColors.success : chartColors.danger
                ),
                borderWidth: 1
            }]
        };

        const config = this.mergeConfig({
            type: 'bar',
            data: chartData,
            options: {
                scales: {
                    y: {
                        title: {
                            display: true,
                            text: 'Return %'
                        },
                        ticks: {
                            callback: function(value) {
                                return value + '%';
                            }
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `Return: ${context.parsed.y.toFixed(2)}%`;
                            }
                        }
                    }
                }
            }
        }, options);

        const chart = new Chart(ctx, config);
        this.charts.set(canvasId, chart);
        
        return chart;
    }

    // Hourly performance chart
    createHourlyPerformanceChart(canvasId, data, options = {}) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        this.destroyChart(canvasId);

        // Create 24-hour array
        const hourlyData = new Array(24).fill(0);
        
        // Populate with actual data
        if (data && Array.isArray(data)) {
            data.forEach(item => {
                const hour = new Date(item.timestamp || item.time).getHours();
                hourlyData[hour] += item.profit || item.pnl || 0;
            });
        }

        const chartData = {
            labels: Array.from({length: 24}, (_, i) => `${i.toString().padStart(2, '0')}:00`),
            datasets: [{
                label: 'Hourly P&L',
                data: hourlyData,
                backgroundColor: hourlyData.map(value => 
                    value >= 0 ? chartColors.success : chartColors.danger
                ),
                borderColor: hourlyData.map(value => 
                    value >= 0 ? chartColors.success : chartColors.danger
                ),
                borderWidth: 1
            }]
        };

        const config = this.mergeConfig({
            type: 'bar',
            data: chartData,
            options: {
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Hour of Day'
                        }
                    },
                    y: {
                        currency: true,
                        title: {
                            display: true,
                            text: 'P&L'
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        }, options);

        const chart = new Chart(ctx, config);
        this.charts.set(canvasId, chart);
        
        return chart;
    }

    // Real-time line chart for live data
    createRealTimeChart(canvasId, options = {}) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        this.destroyChart(canvasId);

        const chartData = {
            labels: [],
            datasets: [{
                label: 'Live Data',
                data: [],
                borderColor: chartColors.primary,
                backgroundColor: chartColors.primary + '20',
                borderWidth: 2,
                fill: false,
                tension: 0.3,
                pointRadius: 0,
                pointHoverRadius: 4
            }]
        };

        const config = this.mergeConfig({
            type: 'line',
            data: chartData,
            options: {
                animation: {
                    duration: 0 // Disable animations for real-time updates
                },
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            unit: 'minute',
                            displayFormats: {
                                minute: 'HH:mm'
                            }
                        },
                        title: {
                            display: true,
                            text: 'Time'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Value'
                        }
                    }
                }
            }
        }, options);

        const chart = new Chart(ctx, config);
        this.charts.set(canvasId, chart);
        
        return chart;
    }

    // Utility methods
    groupDataByMonth(data) {
        const monthlyData = {};
        
        data.forEach(item => {
            const date = new Date(item.date || item.timestamp);
            const monthKey = date.toLocaleDateString('en-US', { year: 'numeric', month: 'short' });
            
            if (!monthlyData[monthKey]) {
                monthlyData[monthKey] = 0;
            }
            
            monthlyData[monthKey] += (item.profit || item.pnl || item.return || 0);
        });
        
        return monthlyData;
    }

    mergeConfig(baseConfig, customConfig) {
        return {
            ...baseConfig,
            options: {
                ...defaultChartConfig,
                ...baseConfig.options,
                ...customConfig
            }
        };
    }

    updateChart(canvasId, newData, datasetIndex = 0) {
        const chart = this.charts.get(canvasId);
        if (!chart) return false;

        if (Array.isArray(newData)) {
            chart.data.datasets[datasetIndex].data = newData;
        } else if (typeof newData === 'object') {
            if (newData.labels) {
                chart.data.labels = newData.labels;
            }
            if (newData.datasets) {
                newData.datasets.forEach((dataset, index) => {
                    if (chart.data.datasets[index]) {
                        Object.assign(chart.data.datasets[index], dataset);
                    }
                });
            }
        }

        chart.update('none'); // No animation for real-time updates
        return true;
    }

    addDataPoint(canvasId, label, value, datasetIndex = 0, maxPoints = 50) {
        const chart = this.charts.get(canvasId);
        if (!chart) return false;

        chart.data.labels.push(label);
        chart.data.datasets[datasetIndex].data.push(value);

        // Limit data points to prevent performance issues
        if (chart.data.labels.length > maxPoints) {
            chart.data.labels.shift();
            chart.data.datasets[datasetIndex].data.shift();
        }

        chart.update('none');
        return true;
    }

    destroyChart(canvasId) {
        const existingChart = this.charts.get(canvasId);
        if (existingChart) {
            existingChart.destroy();
            this.charts.delete(canvasId);
        }
    }

    destroyAllCharts() {
        this.charts.forEach((chart, canvasId) => {
            chart.destroy();
        });
        this.charts.clear();
    }

    getChart(canvasId) {
        return this.charts.get(canvasId);
    }

    getAllCharts() {
        return Array.from(this.charts.values());
    }
}

// Utility functions
function formatCurrency(amount, currency = 'USD') {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currency,
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(amount || 0);
}

function formatPercentage(value) {
    return new Intl.NumberFormat('en-US', {
        style: 'percent',
        minimumFractionDigits: 1,
        maximumFractionDigits: 2
    }).format((value || 0) / 100);
}

// Create global chart manager instance
const chartManager = new ChartManager();

// Export for use in other modules
if (typeof window !== 'undefined') {
    window.chartManager = chartManager;
    window.ChartManager = ChartManager;
    window.chartColors = chartColors;
}

// Chart resize handler
window.addEventListener('resize', () => {
    chartManager.getAllCharts().forEach(chart => {
        chart.resize();
    });
});

// Export for Node.js if needed
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        ChartManager,
        chartManager,
        chartColors,
        formatCurrency,
        formatPercentage
    };
}
