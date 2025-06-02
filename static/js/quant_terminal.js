// The Quant Terminal - Market Manipulation JavaScript
// Advanced controls for The Quant's market manipulation capabilities

document.addEventListener('DOMContentLoaded', function() {
    // Initialize The Quant Terminal
    console.log('⚡ The Quant Terminal initializing...');
    initializeQuantTerminal();
    
    // Auto-refresh market data every 30 seconds
    setInterval(refreshMarketData, 30000);
});

function initializeQuantTerminal() {
    // Bind manipulation control buttons
    bindControlButtons();
    
    // Initialize market data refresh
    refreshMarketData();
    
    // Log terminal initialization
    logQuantAction('SYSTEM', 'The Quant Terminal initialized successfully', 'info');
}

function bindControlButtons() {
    // Performer Status Manipulation
    const changeStatusBtn = document.getElementById('changeStatusBtn');
    if (changeStatusBtn) {
        changeStatusBtn.addEventListener('click', manipulatePerformerStatus);
    }
    
    // Force Transfer
    const forceTransferBtn = document.getElementById('forceTransferBtn');
    if (forceTransferBtn) {
        forceTransferBtn.addEventListener('click', forceUserTransfer);
    }
    
    // Force Redistribution
    const forceRedistributionBtn = document.getElementById('forceRedistributionBtn');
    if (forceRedistributionBtn) {
        forceRedistributionBtn.addEventListener('click', forceMarketRedistribution);
    }
    
    // Mass Transfer Controls
    const performersToAudienceBtn = document.getElementById('performersToAudienceBtn');
    if (performersToAudienceBtn) {
        performersToAudienceBtn.addEventListener('click', forcePerformersToAudience);
    }
    
    const audienceToPerformersBtn = document.getElementById('audienceToPerformersBtn');
    if (audienceToPerformersBtn) {
        audienceToPerformersBtn.addEventListener('click', forceAudienceToPerformers);
    }
    
    // Market Intelligence Controls
    const refreshStatsBtn = document.getElementById('refreshStatsBtn');
    if (refreshStatsBtn) {
        refreshStatsBtn.addEventListener('click', refreshMarketData);
    }
    
    const getAllUsersBtn = document.getElementById('getAllUsersBtn');
    if (getAllUsersBtn) {
        getAllUsersBtn.addEventListener('click', getAllUsers);
    }
    
    const getMarketStatsBtn = document.getElementById('getMarketStatsBtn');
    if (getMarketStatsBtn) {
        getMarketStatsBtn.addEventListener('click', getDetailedMarketStats);
    }
}

async function manipulatePerformerStatus() {
    const username = document.getElementById('statusUsername').value.trim();
    const isPerformer = document.getElementById('statusType').value === 'true';
    const reason = document.getElementById('statusReason').value.trim() || 'Market manipulation by The Quant';
    
    if (!username) {
        showQuantStatus('Username required for status manipulation', 'error');
        return;
    }
    
    try {
        showQuantStatus('⚡ Manipulating performer status...', 'info');
        
        const response = await fetch(`/api/quant/users/${username}/performer-status`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                is_performer: isPerformer,
                reason: reason
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            const statusType = isPerformer ? 'PERFORMER' : 'AUDIENCE';
            logQuantAction('STATUS_MANIPULATION', `Changed ${username} to ${statusType} status`, 'manipulation');
            showQuantStatus(`✅ Successfully manipulated ${username} to ${statusType} status`, 'success');
            
            // Clear form
            document.getElementById('statusUsername').value = '';
            document.getElementById('statusReason').value = '';
            
            // Refresh market data
            setTimeout(refreshMarketData, 1000);
        } else {
            throw new Error(data.error || 'Status manipulation failed');
        }
    } catch (error) {
        console.error('Status manipulation error:', error);
        logQuantAction('ERROR', `Status manipulation failed: ${error.message}`, 'error');
        showQuantStatus(`❌ Status manipulation failed: ${error.message}`, 'error');
    }
}

async function forceUserTransfer() {
    const sender = document.getElementById('transferSender').value.trim();
    const recipient = document.getElementById('transferRecipient').value.trim();
    const amount = parseInt(document.getElementById('transferAmount').value);
    const reason = document.getElementById('transferReason').value.trim() || 'Forced transfer by The Quant';
    
    if (!sender || !recipient || !amount || amount <= 0) {
        showQuantStatus('Valid sender, recipient, and positive amount required', 'error');
        return;
    }
    
    if (sender === recipient) {
        showQuantStatus('Sender and recipient cannot be the same', 'error');
        return;
    }
    
    try {
        showQuantStatus('💸 Forcing transfer...', 'info');
        
        const response = await fetch('/api/quant/force-transfer', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                sender: sender,
                recipient: recipient,
                amount: amount,
                reason: reason
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            logQuantAction('FORCED_TRANSFER', `Forced ${amount} coins from ${sender} to ${recipient}`, 'manipulation');
            showQuantStatus(`✅ Successfully forced transfer of ${amount} coins from ${sender} to ${recipient}`, 'success');
            
            // Clear form
            document.getElementById('transferSender').value = '';
            document.getElementById('transferRecipient').value = '';
            document.getElementById('transferAmount').value = '';
            document.getElementById('transferReason').value = '';
            
            // Refresh market data
            setTimeout(refreshMarketData, 1000);
        } else {
            throw new Error(data.error || 'Forced transfer failed');
        }
    } catch (error) {
        console.error('Forced transfer error:', error);
        logQuantAction('ERROR', `Forced transfer failed: ${error.message}`, 'error');
        showQuantStatus(`❌ Forced transfer failed: ${error.message}`, 'error');
    }
}

async function forceMarketRedistribution() {
    const multiplier = parseFloat(document.getElementById('redistributionMultiplier').value) || 1;
    const reason = document.getElementById('redistributionReason').value.trim() || 'Forced redistribution by The Quant';
    
    if (multiplier <= 0 || multiplier > 10) {
        showQuantStatus('Multiplier must be between 0.1 and 10', 'error');
        return;
    }
    
    try {
        showQuantStatus('⚡ Forcing market redistribution...', 'info');
        
        const response = await fetch('/api/quant/force-redistribution', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                multiplier: multiplier,
                reason: reason
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            logQuantAction('FORCED_REDISTRIBUTION', `Forced ${data.redistributions?.length || 0} redistribution cycles (${multiplier}x)`, 'manipulation');
            showQuantStatus(`✅ Successfully forced redistribution (${multiplier}x multiplier, ${data.total_redistributed || 0} coins redistributed)`, 'success');
            
            // Clear form
            document.getElementById('redistributionReason').value = '';
            document.getElementById('redistributionMultiplier').value = '1';
            
            // Refresh market data
            setTimeout(refreshMarketData, 1000);
        } else {
            throw new Error(data.error || 'Forced redistribution failed');
        }
    } catch (error) {
        console.error('Forced redistribution error:', error);
        logQuantAction('ERROR', `Forced redistribution failed: ${error.message}`, 'error');
        showQuantStatus(`❌ Forced redistribution failed: ${error.message}`, 'error');
    }
}

async function forcePerformersToAudience() {
    const amount = parseInt(document.getElementById('performersToAudienceAmount').value);
    const reason = document.getElementById('performersToAudienceReason').value.trim() || 'Mass performer-to-audience transfer by The Quant';
    
    if (!amount || amount <= 0) {
        showQuantStatus('Valid positive amount required', 'error');
        return;
    }
    
    try {
        showQuantStatus('🎪➡️👥 Forcing mass transfer from performers to audience...', 'info');
        
        const response = await fetch('/api/quant/performers-to-audience', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                amount: amount,
                reason: reason
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            logQuantAction('MASS_TRANSFER', `Forced ${data.transfers?.length || 0} transfers from performers to audience (${amount} coins each)`, 'manipulation');
            showQuantStatus(`✅ Successfully forced ${data.transfers?.length || 0} transfers from performers to audience`, 'success');
            
            if (data.failed_transfers && data.failed_transfers.length > 0) {
                logQuantAction('WARNING', `${data.failed_transfers.length} transfers failed due to insufficient funds`, 'warning');
            }
            
            // Clear form
            document.getElementById('performersToAudienceReason').value = '';
            
            // Refresh market data
            setTimeout(refreshMarketData, 1000);
        } else {
            throw new Error(data.error || 'Mass transfer failed');
        }
    } catch (error) {
        console.error('Mass transfer error:', error);
        logQuantAction('ERROR', `Mass transfer failed: ${error.message}`, 'error');
        showQuantStatus(`❌ Mass transfer failed: ${error.message}`, 'error');
    }
}

async function forceAudienceToPerformers() {
    const amount = parseInt(document.getElementById('audienceToPerformersAmount').value);
    const reason = document.getElementById('audienceToPerformersReason').value.trim() || 'Mass audience-to-performer transfer by The Quant';
    
    if (!amount || amount <= 0) {
        showQuantStatus('Valid positive amount required', 'error');
        return;
    }
    
    try {
        showQuantStatus('👥➡️🎪 Forcing reverse transfer from audience to performers...', 'info');
        
        const response = await fetch('/api/quant/audience-to-performers', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                amount: amount,
                reason: reason
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            logQuantAction('REVERSE_TRANSFER', `Forced ${data.transfers?.length || 0} transfers from audience to performers (${amount} coins each)`, 'manipulation');
            showQuantStatus(`✅ Successfully forced ${data.transfers?.length || 0} transfers from audience to performers`, 'success');
            
            if (data.failed_transfers && data.failed_transfers.length > 0) {
                logQuantAction('WARNING', `${data.failed_transfers.length} transfers failed due to insufficient funds`, 'warning');
            }
            
            // Clear form
            document.getElementById('audienceToPerformersReason').value = '';
            
            // Refresh market data
            setTimeout(refreshMarketData, 1000);
        } else {
            throw new Error(data.error || 'Reverse transfer failed');
        }
    } catch (error) {
        console.error('Reverse transfer error:', error);
        logQuantAction('ERROR', `Reverse transfer failed: ${error.message}`, 'error');
        showQuantStatus(`❌ Reverse transfer failed: ${error.message}`, 'error');
    }
}

async function refreshMarketData() {
    try {
        // Get current market stats from the API
        const response = await fetch('/api/leaderboard');
        if (response.ok) {
            const data = await response.json();
            
            // Update live market data display
            updateMarketDataDisplay(data);
            
            logQuantAction('DATA_REFRESH', 'Market data refreshed successfully', 'info');
        }
    } catch (error) {
        console.error('Market data refresh error:', error);
        logQuantAction('ERROR', `Market data refresh failed: ${error.message}`, 'error');
    }
}

async function getAllUsers() {
    try {
        showQuantStatus('👥 Loading all users...', 'info');
        
        const response = await fetch('/api/quant/users');
        const data = await response.json();
        
        if (response.ok) {
            displayUsersList(data.users);
            logQuantAction('USER_QUERY', `Retrieved ${data.users.length} users`, 'info');
            showQuantStatus(`✅ Loaded ${data.users.length} users`, 'success');
        } else {
            throw new Error(data.error || 'Failed to get users');
        }
    } catch (error) {
        console.error('Get users error:', error);
        logQuantAction('ERROR', `Get users failed: ${error.message}`, 'error');
        showQuantStatus(`❌ Failed to get users: ${error.message}`, 'error');
    }
}

async function getDetailedMarketStats() {
    try {
        showQuantStatus('📊 Loading detailed market statistics...', 'info');
        
        const response = await fetch('/api/quant/market-stats');
        const data = await response.json();
        
        if (response.ok) {
            displayDetailedStats(data.market_stats);
            logQuantAction('MARKET_ANALYSIS', 'Detailed market stats retrieved', 'info');
            showQuantStatus('✅ Detailed market statistics loaded', 'success');
        } else {
            throw new Error(data.error || 'Failed to get market stats');
        }
    } catch (error) {
        console.error('Market stats error:', error);
        logQuantAction('ERROR', `Market stats failed: ${error.message}`, 'error');
        showQuantStatus(`❌ Failed to get market stats: ${error.message}`, 'error');
    }
}

function updateMarketDataDisplay(data) {
    if (data.market_cap !== undefined) {
        const totalCoinsEl = document.getElementById('totalCoins');
        if (totalCoinsEl) totalCoinsEl.textContent = data.market_cap.toLocaleString();
        
        // Update the main market cap display
        const marketCapEls = document.querySelectorAll('[data-stat="market-cap"]');
        marketCapEls.forEach(el => el.textContent = data.market_cap.toLocaleString());
    }
    
    if (data.user_count !== undefined) {
        const totalUsersEl = document.getElementById('totalUsers');
        if (totalUsersEl) totalUsersEl.textContent = data.user_count;
        
        // Update the main user count display
        const userCountEls = document.querySelectorAll('[data-stat="user-count"]');
        userCountEls.forEach(el => el.textContent = data.user_count);
    }
    
    if (data.volume !== undefined) {
        const volumeEls = document.querySelectorAll('[data-stat="volume"]');
        volumeEls.forEach(el => el.textContent = data.volume.toLocaleString());
    }
}

function displayUsersList(users) {
    const usersListEl = document.getElementById('usersListDisplay');
    if (!usersListEl) return;
    
    if (!users || users.length === 0) {
        usersListEl.innerHTML = '<p class="text-center opacity-70">No users found</p>';
        return;
    }
    
    let html = '<div style="display: grid; gap: 10px; max-height: 400px; overflow-y: auto;">';
    
    users.forEach(user => {
        const userType = user.is_performer ? '🎪 Performer' : '👥 Audience';
        const createdDate = user.created_at ? new Date(user.created_at).toLocaleDateString() : 'Unknown';
        
        html += `
            <div style="display: flex; justify-content: space-between; align-items: center; background: rgba(255,255,255,0.1); padding: 15px; border-radius: 8px;">
                <div>
                    <span style="font-weight: bold;">${user.is_performer ? '🎪' : '👥'} ${user.username}</span>
                    <div style="font-size: 0.9rem; opacity: 0.8;">
                        ${userType} | Joined: ${createdDate}
                    </div>
                </div>
                <span style="font-weight: bold; font-size: 1.1rem;">
                    ${user.coin_balance.toLocaleString()} coins
                </span>
            </div>
        `;
    });
    
    html += '</div>';
    usersListEl.innerHTML = html;
}

function displayDetailedStats(stats) {
    const modalContent = `
        <div style="background: rgba(0,0,0,0.9); position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: 1000; display: flex; align-items: center; justify-content: center;" onclick="this.remove()">
            <div style="background: #2c3e50; padding: 30px; border-radius: 15px; max-width: 600px; max-height: 80%; overflow-y: auto;" onclick="event.stopPropagation()">
                <h2 style="color: #ecf0f1; margin-bottom: 20px;">📊 Detailed Market Statistics</h2>
                <div style="color: #ecf0f1;">
                    <p><strong>Total Coins:</strong> ${stats.total_coins?.toLocaleString() || 'N/A'}</p>
                    <p><strong>Total Users:</strong> ${stats.total_users || 'N/A'}</p>
                    <p><strong>Performers:</strong> ${stats.total_performers || 'N/A'}</p>
                    <p><strong>Audience Members:</strong> ${stats.total_audience || 'N/A'}</p>
                    <p><strong>Total Transactions:</strong> ${stats.total_transactions || 'N/A'}</p>
                    <p><strong>Average Balance:</strong> ${stats.average_balance?.toLocaleString() || 'N/A'}</p>
                    <p><strong>Median Balance:</strong> ${stats.median_balance?.toLocaleString() || 'N/A'}</p>
                    <p><strong>Richest User Balance:</strong> ${stats.max_balance?.toLocaleString() || 'N/A'}</p>
                    <p><strong>Poorest User Balance:</strong> ${stats.min_balance?.toLocaleString() || 'N/A'}</p>
                </div>
                <button onclick="this.parentElement.parentElement.remove()" style="background: #e74c3c; color: white; border: none; padding: 10px 20px; border-radius: 5px; margin-top: 20px; cursor: pointer;">Close</button>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalContent);
}

function logQuantAction(type, message, level = 'info') {
    const logEl = document.getElementById('quantLog');
    if (!logEl) return;
    
    const timestamp = new Date().toLocaleTimeString();
    const logClass = `log-${level}`;
    
    const logEntry = document.createElement('div');
    logEntry.className = `log-entry ${logClass}`;
    logEntry.innerHTML = `
        <span class="log-timestamp">[${timestamp}]</span>
        <span class="log-type">[${type}]</span>
        <span class="log-message">${message}</span>
    `;
    
    logEl.appendChild(logEntry);
    
    // Keep only last 50 log entries
    const entries = logEl.querySelectorAll('.log-entry');
    if (entries.length > 50) {
        entries[0].remove();
    }
    
    // Auto-scroll to bottom
    logEl.scrollTop = logEl.scrollHeight;
}

function showQuantStatus(message, type = 'info') {
    const statusEl = document.getElementById('quantStatus');
    if (!statusEl) return;
    
    statusEl.textContent = message;
    statusEl.className = `message message-${type}`;
    
    // Clear after 5 seconds for non-error messages
    if (type !== 'error') {
        setTimeout(() => {
            statusEl.textContent = '';
            statusEl.className = 'message';
        }, 5000);
    }
}

// Enhanced error handling for The Quant's operations
window.addEventListener('error', function(event) {
    logQuantAction('SYSTEM_ERROR', `JavaScript error: ${event.error?.message || 'Unknown error'}`, 'error');
});

// Handle session management for The Quant
function checkQuantSession() {
    fetch('/auth/session-status')
        .then(response => response.json())
        .then(data => {
            if (!data.authenticated) {
                logQuantAction('SESSION', 'Session expired - redirecting to login', 'error');
                window.location.href = '/register';
            }
        })
        .catch(error => {
            console.error('Session check failed:', error);
        });
}

// Check session every 2 minutes
setInterval(checkQuantSession, 120000);