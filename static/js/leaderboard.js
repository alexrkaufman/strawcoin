// Straw Coin Trading Platform JavaScript

let chart;
let updateInterval;
let currentUsername = '';
let chartType = 'line';
let lastUpdateData = null;

document.addEventListener('DOMContentLoaded', function() {
    // Get current username from the page
    const usernameElement = document.querySelector('[data-username]');
    if (usernameElement) {
        currentUsername = usernameElement.getAttribute('data-username');
    }

    initializeChart();
    startAutoUpdate();
    setupTradingControls();

    // Event listeners
    const timeRangeSelect = document.getElementById('timeRangeSelect');
    if (timeRangeSelect) {
        timeRangeSelect.addEventListener('change', function() {
            loadChartData();
        });
    }

    const refreshBtn = document.getElementById('refreshBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            loadChartData();
        });
    }
});

function setupTradingControls() {
    // Chart type buttons
    const chartTypeButtons = document.querySelectorAll('.chart-type-btn');
    chartTypeButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            chartTypeButtons.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            chartType = this.dataset.type;
            // For now, keep line chart (candle charts would need more complex implementation)
        });
    });

    // Auto scale button
    const autoScaleBtn = document.getElementById('autoScale');
    if (autoScaleBtn) {
        autoScaleBtn.addEventListener('click', function() {
            if (chart) {
                chart.resetZoom();
            }
        });
    }
}

function initializeChart() {
    const ctx = document.getElementById('leaderboardChart');
    if (!ctx) return;

    chart = new Chart(ctx.getContext('2d'), {
        type: 'line',
        data: {
            datasets: []
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            backgroundColor: 'transparent',
            plugins: {
                title: {
                    display: false
                },
                legend: {
                    position: 'top',
                    labels: {
                        color: '#ffffff',
                        usePointStyle: true,
                        pointStyle: 'circle',
                        padding: 20,
                        font: {
                            size: 11,
                            weight: 'bold'
                        }
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0,0,0,0.9)',
                    titleColor: '#ffffff',
                    bodyColor: '#ffffff',
                    borderColor: '#4a90e2',
                    borderWidth: 1,
                    displayColors: true,
                    callbacks: {
                        title: function(context) {
                            return new Date(context[0].parsed.x).toLocaleString();
                        },
                        label: function(context) {
                            return context.dataset.label + ': ' + context.parsed.y.toLocaleString() + ' STRAW';
                        }
                    }
                }
            },
            scales: {
                x: {
                    type: 'time',
                    time: {
                        displayFormats: {
                            minute: 'HH:mm',
                            hour: 'HH:mm'
                        }
                    },
                    grid: {
                        color: 'rgba(255,255,255,0.1)',
                        drawBorder: false
                    },
                    ticks: {
                        color: '#b0b0b0',
                        maxTicksLimit: 8,
                        font: {
                            size: 10
                        }
                    },
                    border: {
                        display: false
                    }
                },
                y: {
                    position: 'right',
                    grid: {
                        color: 'rgba(255,255,255,0.1)',
                        drawBorder: false
                    },
                    ticks: {
                        color: '#b0b0b0',
                        callback: function(value) {
                            return value.toLocaleString();
                        },
                        font: {
                            size: 10
                        }
                    },
                    border: {
                        display: false
                    }
                }
            },
            interaction: {
                intersect: false,
                mode: 'index'
            },
            animation: {
                duration: 300,
                easing: 'easeInOutQuart'
            },
            onHover: (event, activeElements) => {
                if (activeElements.length > 0) {
                    const chart = activeElements[0].element.chart;
                    const canvasPosition = Chart.helpers.getRelativePosition(event, chart);
                    const dataX = chart.scales.x.getValueForPixel(canvasPosition.x);
                    const dataY = chart.scales.y.getValueForPixel(canvasPosition.y);
                    
                    const crosshairInfo = document.getElementById('crosshairInfo');
                    if (crosshairInfo) {
                        crosshairInfo.style.display = 'block';
                        document.getElementById('crosshairPrice').textContent = `Price: ${Math.round(dataY).toLocaleString()} STRAW`;
                        document.getElementById('crosshairTime').textContent = `Time: ${new Date(dataX).toLocaleTimeString()}`;
                    }
                } else {
                    const crosshairInfo = document.getElementById('crosshairInfo');
                    if (crosshairInfo) {
                        crosshairInfo.style.display = 'none';
                    }
                }
            }
        }
    });

    loadChartData();
}

async function loadChartData() {
    const timeRangeSelect = document.getElementById('timeRangeSelect');
    const timeRange = timeRangeSelect ? timeRangeSelect.value : '0.5';
    const statusDiv = document.getElementById('chartStatus');
    const refreshBtn = document.getElementById('refreshBtn');

    try {
        if (statusDiv) statusDiv.textContent = 'Loading latest market data...';
        if (refreshBtn) {
            refreshBtn.textContent = '🔄 Loading...';
            refreshBtn.disabled = true;
        }

        const response = await fetch(`/api/leaderboard-history?hours=${timeRange}`);
        const data = await response.json();

        if (data.status === 'success') {
            // Update chart
            if (chart) {
                chart.data.datasets = data.datasets;
                chart.update('active');
            }

            // Update current leaderboard
            updateCurrentLeaderboard(data.current_leaders);

            // Update trading stats
            updateTradingStats(data);

            // Update user position and portfolio
            updateUserPosition(data.current_leaders);
            updatePortfolioMetrics(data);

            // Update market status
            updateMarketStatus(data);

            if (statusDiv) {
                statusDiv.textContent = `${data.datasets.length} instruments • ${data.total_data_points} ticks • ${timeRange}H timeframe`;
            }

            const totalDataPointsElement = document.getElementById('totalDataPoints');
            if (totalDataPointsElement) {
                totalDataPointsElement.textContent = data.total_data_points.toLocaleString();
            }

            const updateTimeElement = document.getElementById('updateTime');
            if (updateTimeElement) {
                updateTimeElement.textContent = new Date().toLocaleTimeString();
            }

            // Store for comparison
            lastUpdateData = data;
        } else {
            if (statusDiv) statusDiv.textContent = 'Error loading chart data';
        }
    } catch (error) {
        console.error('Chart data error:', error);
        if (statusDiv) statusDiv.textContent = 'Network error - retrying...';
    } finally {
        if (refreshBtn) {
            refreshBtn.textContent = '🔄 Refresh Data';
            refreshBtn.disabled = false;
        }
    }
}

function updateCurrentLeaderboard(leaders) {
    const container = document.getElementById('currentLeaderboard');
    if (!container || !leaders) return;

    container.innerHTML = '';

    leaders.slice(0, 15).forEach((leader, index) => {
        const div = document.createElement('div');
        
        // Calculate 24h change (mock data for now)
        const change24h = (Math.sin(index * 0.5) * 3 + Math.random() * 2 - 1).toFixed(2);
        const isPositive = change24h >= 0;
        
        const isCurrentUser = leader.username === currentUsername;
        
        div.style.cssText = `
            display: grid; 
            grid-template-columns: 60px 2fr 1fr 1fr; 
            gap: 15px; 
            padding: 12px 15px; 
            border-radius: 6px; 
            margin-bottom: 8px;
            transition: all 0.3s;
            background: ${isCurrentUser ? 'rgba(74, 144, 226, 0.2)' : 'rgba(255,255,255,0.02)'};
            border: ${isCurrentUser ? '1px solid rgba(74, 144, 226, 0.5)' : '1px solid transparent'};
        `;
        
        div.addEventListener('mouseenter', () => {
            if (!isCurrentUser) {
                div.style.background = 'rgba(255,255,255,0.05)';
            }
        });
        
        div.addEventListener('mouseleave', () => {
            if (!isCurrentUser) {
                div.style.background = 'rgba(255,255,255,0.02)';
            }
        });

        const rankSymbol = index === 0 ? '👑' : index === 1 ? '🥈' : index === 2 ? '🥉' : (index + 1);

        div.innerHTML = `
            <div style="color: ${index < 3 ? '#FFA726' : '#b0b0b0'}; font-weight: bold; display: flex; align-items: center;">
                ${rankSymbol}
            </div>
            <div style="color: ${isCurrentUser ? '#4a90e2' : '#ffffff'}; font-weight: ${isCurrentUser ? 'bold' : 'normal'}; display: flex; align-items: center;">
                ${leader.username}
                ${isCurrentUser ? ' <span style="color: #00D084; font-size: 0.8rem; margin-left: 8px;">YOU</span>' : ''}
            </div>
            <div style="color: #ffffff; font-weight: bold; text-align: right; display: flex; align-items: center; justify-content: flex-end;">
                ${leader.coin_balance.toLocaleString()}
            </div>
            <div style="color: ${isPositive ? '#00D084' : '#F23645'}; font-weight: bold; text-align: right; display: flex; align-items: center; justify-content: flex-end;">
                ${isPositive ? '+' : ''}${change24h}%
            </div>
        `;

        container.appendChild(div);
    });
}

function updateUserPosition(leaders) {
    const positionElement = document.getElementById('userPosition');
    if (!positionElement || !leaders) return;

    const userPosition = leaders.findIndex(leader => leader.username === currentUsername) + 1;

    if (userPosition > 0) {
        let positionText = `#${userPosition}`;
        if (userPosition === 1) positionText += ' 🥇';
        else if (userPosition === 2) positionText += ' 🥈';
        else if (userPosition === 3) positionText += ' 🥉';

        positionElement.textContent = positionText;
    } else {
        positionElement.textContent = 'Unranked';
    }
}

function updateTradingStats(data) {
    if (!data.datasets) return;

    // Calculate biggest gainer/loser from chart data
    let biggestGain = 0;
    let biggestLoss = 0;
    let biggestGainer = '--';
    let biggestLoser = '--';
    let mostVolatile = '--';
    let maxVolatility = 0;

    data.datasets.forEach(dataset => {
        if (dataset.data.length >= 2) {
            const first = dataset.data[0].y;
            const last = dataset.data[dataset.data.length - 1].y;
            const change = last - first;
            const changePercent = ((change / first) * 100);

            // Calculate volatility (standard deviation of changes)
            let volatility = 0;
            if (dataset.data.length > 5) {
                const changes = [];
                for (let i = 1; i < dataset.data.length; i++) {
                    changes.push(dataset.data[i].y - dataset.data[i-1].y);
                }
                const mean = changes.reduce((a, b) => a + b, 0) / changes.length;
                const variance = changes.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / changes.length;
                volatility = Math.sqrt(variance);
            }

            if (change > biggestGain) {
                biggestGain = change;
                biggestGainer = dataset.label;
            }
            if (change < biggestLoss) {
                biggestLoss = change;
                biggestLoser = dataset.label;
            }
            if (volatility > maxVolatility) {
                maxVolatility = volatility;
                mostVolatile = dataset.label;
            }
        }
    });

    // Update UI with trading platform styling
    const biggestGainerElement = document.getElementById('biggestGainer');
    if (biggestGainerElement) {
        const gainPercent = biggestGain > 0 ? ((biggestGain / 10000) * 100).toFixed(2) : '0.00';
        biggestGainerElement.innerHTML = `
            <p style="color: #ffffff; font-size: 1.4rem; font-weight: bold; margin: 5px 0;">${biggestGainer}</p>
            <p style="color: #00D084; font-size: 1.1rem; font-weight: bold; margin: 0;">+${biggestGain.toLocaleString()} (+${gainPercent}%)</p>
        `;
    }

    const biggestLoserElement = document.getElementById('biggestLoser');
    if (biggestLoserElement) {
        const lossPercent = biggestLoss < 0 ? ((Math.abs(biggestLoss) / 10000) * 100).toFixed(2) : '0.00';
        biggestLoserElement.innerHTML = `
            <p style="color: #ffffff; font-size: 1.4rem; font-weight: bold; margin: 5px 0;">${biggestLoser}</p>
            <p style="color: #F23645; font-size: 1.1rem; font-weight: bold; margin: 0;">${biggestLoss.toLocaleString()} (-${lossPercent}%)</p>
        `;
    }

    // Most active (using volatility as proxy)
    const mostActiveElement = document.getElementById('mostActive');
    if (mostActiveElement) {
        const mockTransactions = Math.floor(maxVolatility / 10) + Math.floor(Math.random() * 5) + 1;
        mostActiveElement.innerHTML = `
            <p style="color: #ffffff; font-size: 1.4rem; font-weight: bold; margin: 5px 0;">${mostVolatile}</p>
            <p style="color: #FFA726; font-size: 1.1rem; font-weight: bold; margin: 0;">${mockTransactions} trades</p>
        `;
    }
}

function updatePortfolioMetrics(data) {
    if (!currentUsername || !data.current_leaders) return;
    
    const userLeader = data.current_leaders.find(leader => leader.username === currentUsername);
    if (!userLeader) return;
    
    // Mock 24h change calculation
    const mockChange = (Math.sin(Date.now() / 100000) * 2 + Math.random() * 1 - 0.5).toFixed(2);
    const isPositive = mockChange >= 0;
    
    const portfolioChangeElement = document.getElementById('portfolioChange');
    if (portfolioChangeElement) {
        portfolioChangeElement.style.color = isPositive ? '#00D084' : '#F23645';
        portfolioChangeElement.textContent = `${isPositive ? '+' : ''}${mockChange}%`;
    }
}

function updateMarketStatus(data) {
    const marketCapElement = document.getElementById('marketCap');
    const volume24hElement = document.getElementById('volume24h');
    const activeTradersElement = document.getElementById('activeTraders');
    
    if (marketCapElement && data.current_leaders) {
        const totalMarketCap = data.current_leaders.reduce((sum, leader) => sum + leader.coin_balance, 0);
        marketCapElement.textContent = totalMarketCap.toLocaleString() + ' STRAW';
    }
    
    if (volume24hElement) {
        // Mock 24h volume
        const mockVolume = Math.floor(Math.random() * 50000) + 100000;
        volume24hElement.textContent = mockVolume.toLocaleString() + ' STRAW';
    }
    
    if (activeTradersElement && data.current_leaders) {
        activeTradersElement.textContent = data.current_leaders.length.toString();
    }
    
    // Check for market status updates
    checkMarketStatus();
}

async function checkMarketStatus() {
    try {
        const response = await fetch('/api/market-status');
        if (response.ok) {
            const data = await response.json();
            updateMarketStatusDisplay(data.market_status);
        }
    } catch (error) {
        console.log('Market status check failed:', error);
    }
}

function updateMarketStatusDisplay(marketStatus) {
    // Find market status elements
    const statusElements = document.querySelectorAll('[style*="MARKET STATUS"]');
    
    statusElements.forEach(element => {
        const statusSpan = element.querySelector('span:last-child');
        const parentDiv = element.parentElement;
        
        if (statusSpan && parentDiv) {
            statusSpan.textContent = marketStatus.status_text;
            parentDiv.style.color = marketStatus.status_color;
            
            // Add redistribution status indicator
            if (!document.getElementById('redistributionStatus')) {
                const redistStatus = document.createElement('div');
                redistStatus.id = 'redistributionStatus';
                redistStatus.style.cssText = 'font-size: 0.8rem; opacity: 0.8; margin-top: 4px;';
                redistStatus.textContent = marketStatus.redistribution_active ? 
                    '⚡ Redistributions Active' : '⏸️ Redistributions Paused';
                element.appendChild(redistStatus);
            } else {
                const redistStatus = document.getElementById('redistributionStatus');
                redistStatus.textContent = marketStatus.redistribution_active ? 
                    '⚡ Redistributions Active' : '⏸️ Redistributions Paused';
            }
        }
    });
}

function startAutoUpdate() {
    // Update every 30 seconds for live trading feel
    updateInterval = setInterval(() => {
        loadChartData();
    }, 30000);
    
    // Update market status more frequently for dynamic feel
    setInterval(() => {
        updateLiveMarketIndicators();
    }, 5000);
}

function updateLiveMarketIndicators() {
    // Add subtle animations to make it feel more "live"
    const liveIndicator = document.querySelector('[style*="animation: pulse"]');
    if (liveIndicator) {
        liveIndicator.style.opacity = Math.random() * 0.3 + 0.7;
    }
    
    // Randomly update volume (small changes)
    const volume24hElement = document.getElementById('volume24h');
    if (volume24hElement && volume24hElement.textContent !== 'Loading...') {
        const currentVolume = parseInt(volume24hElement.textContent.replace(/[^0-9]/g, ''));
        const change = Math.floor(Math.random() * 1000) - 500; // ±500 change
        const newVolume = Math.max(50000, currentVolume + change);
        volume24hElement.textContent = newVolume.toLocaleString() + ' STRAW';
    }
}

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (updateInterval) {
        clearInterval(updateInterval);
    }
});

// Add button hover effects
document.addEventListener('DOMContentLoaded', function() {
    const buttons = document.querySelectorAll('button');
    buttons.forEach(button => {
        button.addEventListener('mouseenter', function() {
            if (!this.disabled) {
                this.style.transform = 'scale(1.05)';
            }
        });

        button.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1)';
        });
    });
});

// Export for global use
window.StrawCoinLeaderboard = {
    loadChartData,
    updateCurrentLeaderboard,
    updateUserPosition
};