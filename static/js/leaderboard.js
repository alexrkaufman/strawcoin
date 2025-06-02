// Straw Coin Leaderboard JavaScript

let chart;
let updateInterval;
let currentUsername = '';

document.addEventListener('DOMContentLoaded', function() {
    // Get current username from the page
    const usernameElement = document.querySelector('[data-username]');
    if (usernameElement) {
        currentUsername = usernameElement.getAttribute('data-username');
    }

    initializeChart();
    startAutoUpdate();

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
            plugins: {
                title: {
                    display: true,
                    text: 'Straw Coin Leaderboard Race',
                    color: '#ffffff',
                    font: {
                        size: 18,
                        weight: 'bold'
                    }
                },
                legend: {
                    labels: {
                        color: '#ffffff',
                        usePointStyle: true
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
                        color: 'rgba(255,255,255,0.1)'
                    },
                    ticks: {
                        color: '#ffffff'
                    },
                    title: {
                        display: true,
                        text: 'Time',
                        color: '#ffffff'
                    }
                },
                y: {
                    grid: {
                        color: 'rgba(255,255,255,0.1)'
                    },
                    ticks: {
                        color: '#ffffff',
                        callback: function(value) {
                            return value.toLocaleString() + ' coins';
                        }
                    },
                    title: {
                        display: true,
                        text: 'Straw Coins',
                        color: '#ffffff'
                    }
                }
            },
            interaction: {
                intersect: false,
                mode: 'index'
            },
            animation: {
                duration: 1000,
                easing: 'easeInOutQuart'
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

            // Update stats
            updateRacingStats(data);

            // Update user position
            updateUserPosition(data.current_leaders);

            if (statusDiv) {
                statusDiv.textContent = `Showing ${data.datasets.length} traders over ${timeRange} hours`;
            }

            const totalDataPointsElement = document.getElementById('totalDataPoints');
            if (totalDataPointsElement) {
                totalDataPointsElement.textContent = data.total_data_points;
            }

            const updateTimeElement = document.getElementById('updateTime');
            if (updateTimeElement) {
                updateTimeElement.textContent = new Date().toLocaleTimeString();
            }
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

    const medals = ['🥇', '🥈', '🥉'];
    container.innerHTML = '';

    leaders.slice(0, 10).forEach((leader, index) => {
        const div = document.createElement('div');
        div.className = 'leaderboard-item';
        
        if (leader.username === currentUsername) {
            div.classList.add('current-user');
        }

        const medal = index < 3 ? medals[index] : `#${index + 1}`;

        div.innerHTML = `
            <span class="font-bold">
                ${medal} ${leader.username}
            </span>
            <span class="font-bold" style="font-size: 1.1rem;">
                ${leader.coin_balance.toLocaleString()} coins
            </span>
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

function updateRacingStats(data) {
    if (!data.datasets) return;

    // Calculate biggest gainer/loser from chart data
    let biggestGain = 0;
    let biggestLoss = 0;
    let biggestGainer = '--';
    let biggestLoser = '--';

    data.datasets.forEach(dataset => {
        if (dataset.data.length >= 2) {
            const first = dataset.data[0].y;
            const last = dataset.data[dataset.data.length - 1].y;
            const change = last - first;

            if (change > biggestGain) {
                biggestGain = change;
                biggestGainer = dataset.label;
            }
            if (change < biggestLoss) {
                biggestLoss = change;
                biggestLoser = dataset.label;
            }
        }
    });

    // Update UI
    const biggestGainerElement = document.getElementById('biggestGainer');
    if (biggestGainerElement) {
        biggestGainerElement.innerHTML = `
            <p style="font-size: 1.5rem; font-weight: bold;">${biggestGainer}</p>
            <p style="color: #2ecc71;">+${biggestGain.toLocaleString()} coins</p>
        `;
    }

    const biggestLoserElement = document.getElementById('biggestLoser');
    if (biggestLoserElement) {
        biggestLoserElement.innerHTML = `
            <p style="font-size: 1.5rem; font-weight: bold;">${biggestLoser}</p>
            <p style="color: #e74c3c;">${biggestLoss.toLocaleString()} coins</p>
        `;
    }

    // Most active (placeholder - would need transaction data)
    const mostActiveElement = document.getElementById('mostActive');
    if (mostActiveElement) {
        mostActiveElement.innerHTML = `
            <p style="font-size: 1.5rem; font-weight: bold;">--</p>
            <p>Feature coming soon</p>
        `;
    }
}

function startAutoUpdate() {
    // Update every 30 seconds
    updateInterval = setInterval(() => {
        loadChartData();
    }, 30000);
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