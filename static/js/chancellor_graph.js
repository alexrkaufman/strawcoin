let chart = null;

// Initialize the chart
function initializeChart() {
    const ctx = document.getElementById('performerChart').getContext('2d');
    
    chart = new Chart(ctx, {
        type: 'line',
        data: {
            datasets: []
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Top 5 Performers - Real-Time Performance',
                    font: {
                        size: 18,
                        weight: 'bold'
                    },
                    color: '#FFD700'
                },
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        color: '#fff',
                        font: {
                            size: 12
                        },
                        usePointStyle: true,
                        padding: 15
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: '#FFD700',
                    bodyColor: '#fff',
                    borderColor: '#FFD700',
                    borderWidth: 1,
                    padding: 10,
                    displayColors: true,
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.parsed.y !== null) {
                                label += context.parsed.y.toLocaleString() + ' 🪙';
                            }
                            return label;
                        }
                    }
                }
            },
            scales: {
                x: {
                    type: 'time',
                    time: {
                        parser: 'YYYY-MM-DDTHH:mm:ss',
                        tooltipFormat: 'MMM DD, HH:mm:ss',
                        displayFormats: {
                            second: 'HH:mm:ss',
                            minute: 'HH:mm',
                            hour: 'HH:mm'
                        }
                    },
                    title: {
                        display: true,
                        text: 'Time',
                        color: '#FFD700',
                        font: {
                            size: 14,
                            weight: 'bold'
                        }
                    },
                    ticks: {
                        color: '#fff',
                        maxRotation: 0,
                        autoSkip: true,
                        maxTicksLimit: 10
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)',
                        drawBorder: false
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Balance (🪙)',
                        color: '#FFD700',
                        font: {
                            size: 14,
                            weight: 'bold'
                        }
                    },
                    ticks: {
                        color: '#fff',
                        callback: function(value) {
                            return value.toLocaleString();
                        }
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)',
                        drawBorder: false
                    }
                }
            }
        }
    });
}

// Fetch and update graph data
async function fetchGraphData() {
    try {
        // Fetch data for last 10 minutes (0.167 hours)
        const response = await fetch('/api/leaderboard-history?hours=0.167');
        const data = await response.json();
        
        if (data.status === 'success') {
            // Get only top 5 performers based on current balance
            const top5 = data.current_leaders.slice(0, 5).map(user => ({
                ...user,
                balance: user.balance || user.coin_balance || 0
            }));
            const top5Usernames = top5.map(user => user.username);
            
            // Filter datasets to only include top 5
            let filteredDatasets = data.datasets.filter(dataset => 
                top5Usernames.includes(dataset.label)
            );
            
            // If there's no historical data, create single-point datasets with current balances
            if (filteredDatasets.length === 0 || filteredDatasets.every(ds => ds.data.length === 0)) {
                const currentTime = new Date().toISOString();
                filteredDatasets = top5.map((user, index) => {
                    const colors = [
                        "#00D084",  // Green (bullish)
                        "#F23645",  // Red (bearish)
                        "#FFA726",  // Orange
                        "#42A5F5",  // Blue
                        "#AB47BC",  // Purple
                    ];
                    
                    return {
                        label: user.username,
                        data: [{
                            x: currentTime,
                            y: user.balance || 0
                        }],
                        borderColor: colors[index % colors.length],
                        backgroundColor: colors[index % colors.length] + "10",
                        tension: 0.1,
                        fill: false,
                        borderWidth: 2,
                        pointRadius: 4,
                        pointHoverRadius: 6,
                    };
                });
                
                console.log('Limited historical data - showing current balances');
            }
            
            // Ensure all datasets have at least the current balance as the most recent point
            filteredDatasets = filteredDatasets.map((dataset, index) => {
                const user = top5.find(u => u.username === dataset.label);
                if (user && dataset.data.length > 0) {
                    // Add current balance as the most recent data point if it's different
                    const lastPoint = dataset.data[dataset.data.length - 1];
                    const currentBalance = user.balance || 0;
                    const currentTime = new Date().toISOString();
                    
                    // Only add if the last point is older than 30 seconds or has different value
                    const lastTime = new Date(lastPoint.x);
                    const timeDiff = new Date() - lastTime;
                    
                    if (timeDiff > 30000 || lastPoint.y !== currentBalance) {
                        dataset.data.push({
                            x: currentTime,
                            y: currentBalance
                        });
                    }
                }
                return dataset;
            });
            
            // Update chart data
            chart.data.datasets = filteredDatasets;
            chart.update('none'); // Update without animation for smoother real-time feel
        }
    } catch (error) {
        console.error('Error fetching graph data:', error);
        console.error('Failed to fetch graph data');
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeChart();
    fetchGraphData();
    
    // Auto-refresh every 5 seconds
    setInterval(() => {
        fetchGraphData();
    }, 5000);
});


