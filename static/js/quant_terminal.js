// The CHANCELLOR Terminal - Market Manipulation JavaScript
// Advanced controls for The CHANCELLOR's market manipulation capabilities

document.addEventListener("DOMContentLoaded", function () {
  // Initialize The CHANCELLOR Terminal
  console.log("🎛️ The CHANCELLOR Terminal initializing...");
  initializeQuantTerminal();

  // Auto-refresh market data
  const marketRefresh = StrawCoinUtils.createAutoRefresh(
    refreshMarketData,
    StrawCoinUtils.REFRESH_INTERVALS.marketStats
  );
  marketRefresh.start();
});

function initializeQuantTerminal() {
  // Bind manipulation control buttons
  bindControlButtons();

  // Initialize market data refresh
  refreshMarketData();
  
  // Load current redistribution rate
  loadCurrentRedistributionRate();
  
  // Load pending offers
  loadPendingOffers();

  // Log terminal initialization
  logQuantAction(
    "SYSTEM",
    "The CHANCELLOR Terminal initialized successfully",
    "info",
  );

  // Get current username
  window.currentUsername = StrawCoinUtils.getCurrentUsername();
}

function bindControlButtons() {
  // Performer Status Manipulation
  const changeStatusBtn = document.getElementById("changeStatusBtn");
  if (changeStatusBtn) {
    changeStatusBtn.addEventListener("click", manipulatePerformerStatus);
  }

  // Universal Force Transfer
  const forceTransferBtn = document.getElementById("forceTransferBtn");
  if (forceTransferBtn) {
    forceTransferBtn.addEventListener("click", executeUniversalTransfer);
  }

  // Update Redistribution Rate
  const updateRedistributionBtn = document.getElementById(
    "updateRedistributionBtn",
  );
  if (updateRedistributionBtn) {
    updateRedistributionBtn.addEventListener("click", updateRedistributionRate);
  }

  // Market Intelligence Controls
  const refreshStatsBtn = document.getElementById("refreshStatsBtn");
  if (refreshStatsBtn) {
    refreshStatsBtn.addEventListener("click", refreshMarketData);
  }

  const getAllUsersBtn = document.getElementById("getAllUsersBtn");
  if (getAllUsersBtn) {
    getAllUsersBtn.addEventListener("click", getAllUsers);
  }

  const getMarketStatsBtn = document.getElementById("getMarketStatsBtn");
  if (getMarketStatsBtn) {
    getMarketStatsBtn.addEventListener("click", getDetailedMarketStats);
  }

  // Market Control
  const toggleMarketBtn = document.getElementById("toggleMarketBtn");
  if (toggleMarketBtn) {
    toggleMarketBtn.addEventListener("click", toggleMarketStatus);
  }
  
  // Pending Offers
  const refreshOffersBtn = document.getElementById("refreshOffersBtn");
  if (refreshOffersBtn) {
    refreshOffersBtn.addEventListener("click", loadPendingOffers);
  }
}

async function manipulatePerformerStatus() {
  const username = document.getElementById("statusUsername").value.trim();
  const isPerformer = document.getElementById("statusType").value === "true";
  const reason =
    document.getElementById("statusReason").value.trim() ||
    "Market manipulation by The CHANCELLOR";

  const validation = StrawCoinUtils.validateUsername(username);
  if (!validation.isValid) {
    showQuantStatus(validation.message, "error");
    return;
  }

  try {
    showQuantStatus("⚡ Manipulating performer status...", "info");

    const data = await StrawCoinUtils.apiRequest(
      `/api/quant/users/${username}/performer-status`,
      {
        method: "PUT",
        body: JSON.stringify({
          is_performer: isPerformer,
          reason: reason,
        }),
      },
    );

    if (data) {
      const statusType = isPerformer ? "PERFORMER" : "AUDIENCE";
      logQuantAction(
        "STATUS_MANIPULATION",
        `Changed ${username} to ${statusType} status`,
        "manipulation",
      );
      showQuantStatus(
        `✅ Successfully manipulated ${username} to ${statusType} status`,
        "success",
      );

      // Clear form
      document.getElementById("statusUsername").value = "";
      document.getElementById("statusReason").value = "";

      // Refresh market data
      setTimeout(refreshMarketData, 1000);
    } else {
      throw new Error(data.error || "Status manipulation failed");
    }
  } catch (error) {
    console.error("Status manipulation error:", error);
    logQuantAction(
      "ERROR",
      `Status manipulation failed: ${error.message}`,
      "error",
    );
    showQuantStatus(`❌ Status manipulation failed: ${error.message}`, "error");
  }
}

async function executeUniversalTransfer() {
  const sender = document.getElementById("transferSender").value.trim();
  const recipient = document.getElementById("transferRecipient").value.trim();
  const amount = parseInt(document.getElementById("transferAmount").value);
  const reason =
    document.getElementById("transferReason").value.trim() ||
    "Universal transfer by The CHANCELLOR";

  if (!sender || !recipient || !amount || amount <= 0) {
    showQuantStatus(
      "Valid sender, recipient, and positive amount required",
      "error",
    );
    return;
  }

  if (sender === recipient) {
    showQuantStatus("Sender and recipient cannot be the same", "error");
    return;
  }

  // Determine transfer type based on sender and recipient
  let transferType = "individual";
  let endpoint = "/api/quant/force-transfer";
  let payload = { sender, recipient, amount, reason };

  if (sender === "All Performers" && recipient === "All Audience") {
    transferType = "performers-to-audience";
    endpoint = "/api/quant/performers-to-audience";
    payload = { amount, reason };
  } else if (sender === "All Audience" && recipient === "All Performers") {
    transferType = "audience-to-performers";
    endpoint = "/api/quant/audience-to-performers";
    payload = { amount, reason };
  } else if (
    sender === "All Performers" ||
    sender === "All Audience" ||
    recipient === "All Performers" ||
    recipient === "All Audience"
  ) {
    // Handle mixed group transfers (one group, one individual)
    transferType = "mixed-group";
    endpoint = "/api/quant/group-transfer";
    payload = { sender, recipient, amount, reason };
  }

  try {
    const statusMessage = getTransferStatusMessage(
      sender,
      recipient,
      amount,
      transferType,
    );
    showQuantStatus(statusMessage, "info");

    const data = await StrawCoinUtils.apiRequest(endpoint, {
      method: "POST",
      body: JSON.stringify(payload),
    });

    if (data) {
      const successMessage = getTransferSuccessMessage(data, transferType);
      logQuantAction("UNIVERSAL_TRANSFER", successMessage, "manipulation");
      showQuantStatus(`✅ ${successMessage}`, "success");

      // Clear form
      document.getElementById("transferSender").value = "";
      document.getElementById("transferRecipient").value = "";
      document.getElementById("transferAmount").value = "";
      document.getElementById("transferReason").value = "";

      // Refresh market data
      setTimeout(refreshMarketData, 1000);
    } else {
      throw new Error(data.error || "Transfer failed");
    }
  } catch (error) {
    console.error("Universal transfer error:", error);
    logQuantAction(
      "ERROR",
      `Universal transfer failed: ${error.message}`,
      "error",
    );
    showQuantStatus(`❌ Transfer failed: ${error.message}`, "error");
  }
}

function getTransferStatusMessage(sender, recipient, amount, type) {
  switch (type) {
    case "performers-to-audience":
      return "🎪➡️👥 Forcing mass transfer from all performers to all audience...";
    case "audience-to-performers":
      return "👥➡️🎪 Forcing reverse transfer from all audience to all performers...";
    case "mixed-group":
      return `💸 Forcing group transfer from ${sender} to ${recipient}...`;
    default:
      return `💸 Forcing transfer from ${sender} to ${recipient}...`;
  }
}

function getTransferSuccessMessage(data, type) {
  switch (type) {
    case "performers-to-audience":
      return `Mass transfer completed: ${data.transfers?.length || 0} transfers from performers to audience`;
    case "audience-to-performers":
      return `Reverse transfer completed: ${data.transfers?.length || 0} transfers from audience to performers`;
    case "mixed-group":
      return `Group transfer completed: ${data.transfers?.length || 0} transfers`;
    default:
      return `Individual transfer completed: ${data.amount} coins from ${data.sender} to ${data.recipient}`;
  }
}

async function updateRedistributionRate() {
  const amount = parseInt(document.getElementById("redistributionAmount").value);

  if (isNaN(amount) || amount < 0 || amount > 1000) {
    showQuantStatus("Amount must be between 0 and 1000", "error");
    return;
  }

  try {
    showQuantStatus("⚡ Updating redistribution rate...", "info");

    const data = await StrawCoinUtils.apiRequest("/api/quant/update-redistribution-amount", {
      method: "POST",
      body: JSON.stringify({
        amount: amount,
      }),
    });

    if (data) {
      // Update the display
      const currentRateEl = document.getElementById("currentRedistributionRate");
      if (currentRateEl) {
        currentRateEl.textContent = amount;
      }

      logQuantAction(
        "REDISTRIBUTION_RATE_CHANGE",
        `Changed redistribution rate to ${amount} coins per performer per minute`,
        "manipulation",
      );
      showQuantStatus(
        `✅ Redistribution rate updated to ${amount} coins per minute`,
        "success",
      );
    } else {
      throw new Error(data.error || "Failed to update redistribution rate");
    }
  } catch (error) {
    console.error("Redistribution rate update error:", error);
    logQuantAction(
      "ERROR",
      `Redistribution rate update failed: ${error.message}`,
      "error",
    );
    showQuantStatus(
      `❌ Failed to update redistribution rate: ${error.message}`,
      "error",
    );
  }
}

async function loadCurrentRedistributionRate() {
  try {
    const data = await StrawCoinUtils.apiRequest("/api/quant/get-redistribution-amount");
    if (data && data.amount !== undefined) {
      const amountInput = document.getElementById("redistributionAmount");
      const currentRateEl = document.getElementById("currentRedistributionRate");
      
      if (amountInput) {
        amountInput.value = data.amount;
      }
      if (currentRateEl) {
        currentRateEl.textContent = data.amount;
      }
    }
  } catch (error) {
    console.error("Failed to load redistribution rate:", error);
  }
}

async function refreshMarketData() {
  try {
    // Get current market stats from the API
    const data = await StrawCoinUtils.apiRequest("/api/leaderboard");
    if (data) {
      // Update live market data display
      updateMarketDataDisplay(data);

      logQuantAction(
        "DATA_REFRESH",
        "Market data refreshed successfully",
        "info",
      );
    }
    
    // Also refresh market status
    const marketData = await StrawCoinUtils.apiRequest("/api/market-status");
    if (marketData && marketData.market_status) {
      const marketStatusIndicator = document.getElementById("marketStatusIndicator");
      if (marketStatusIndicator) {
        marketStatusIndicator.textContent = marketData.market_status.status_text;
        marketStatusIndicator.style.color = marketData.market_status.status_color;
      }
      
      // Update the select dropdown
      const marketStateSelect = document.getElementById("marketStateSelect");
      if (marketStateSelect) {
        marketStateSelect.value = marketData.market_status.is_open ? "open" : "closed";
      }
    }
  } catch (error) {
    console.error("Market data refresh error:", error);
    logQuantAction(
      "ERROR",
      `Market data refresh failed: ${error.message}`,
      "error",
    );
  }
}

async function getAllUsers() {
  try {
    showQuantStatus("👥 Loading all users...", "info");

    const data = await StrawCoinUtils.apiRequest("/api/quant/users");

    if (data) {
      displayUsersList(data.users);
      logQuantAction(
        "USER_QUERY",
        `Retrieved ${data.users.length} users`,
        "info",
      );
      showQuantStatus(`✅ Loaded ${data.users.length} users`, "success");
    } else {
      throw new Error(data.error || "Failed to get users");
    }
  } catch (error) {
    console.error("Get users error:", error);
    logQuantAction("ERROR", `Get users failed: ${error.message}`, "error");
    showQuantStatus(`❌ Failed to get users: ${error.message}`, "error");
  }
}

async function getDetailedMarketStats() {
  try {
    showQuantStatus("📊 Loading detailed market statistics...", "info");

    const data = await StrawCoinUtils.apiRequest("/api/quant/market-stats");

    if (data) {
      displayDetailedStats(data.market_stats);
      logQuantAction(
        "MARKET_ANALYSIS",
        "Detailed market stats retrieved",
        "info",
      );
      showQuantStatus("✅ Detailed market statistics loaded", "success");
    } else {
      throw new Error(data.error || "Failed to get market stats");
    }
  } catch (error) {
    console.error("Market stats error:", error);
    logQuantAction("ERROR", `Market stats failed: ${error.message}`, "error");
    showQuantStatus(`❌ Failed to get market stats: ${error.message}`, "error");
  }
}

function updateMarketDataDisplay(data) {
  StrawCoinUtils.updateMarketStats(data);
}

function displayUsersList(users) {
  const usersListEl = document.getElementById("usersListDisplay");
  if (!usersListEl) return;

  if (!users || users.length === 0) {
    usersListEl.innerHTML =
      '<p class="text-center opacity-70">No users found</p>';
    return;
  }

  let html = '<div>';

  users.forEach((user) => {
    const userType = user.is_performer ? "🎪 Performer" : "👥 Audience";
    const createdDate = user.created_at
      ? new Date(user.created_at).toLocaleDateString()
      : "Unknown";

    html += `
            <div class="list-item">
                <div>
                    <span class="user-name">${user.is_performer ? "🎪" : "👥"} ${user.username}</span>
                    <div class="text-xs opacity-80">
                        ${userType} | Joined: ${createdDate}
                    </div>
                </div>
                <span class="user-balance">
                    ${StrawCoinUtils.formatNumber(user.coin_balance, 'coins')}
                </span>
            </div>
        `;
  });

  html += "</div>";
  usersListEl.innerHTML = html;
}

function displayDetailedStats(stats) {
  const modalContent = `
    <h2 style="color: #ecf0f1; margin-bottom: 20px;">📊 Detailed Market Statistics</h2>
    <div style="color: #ecf0f1;">
        <p><strong>Total Coins:</strong> ${StrawCoinUtils.formatNumber(stats.total_coins)}</p>
        <p><strong>Total Users:</strong> ${stats.total_users || "N/A"}</p>
        <p><strong>Performers:</strong> ${stats.total_performers || "N/A"}</p>
        <p><strong>Audience Members:</strong> ${stats.total_audience || "N/A"}</p>
        <p><strong>Total Transactions:</strong> ${stats.total_transactions || "N/A"}</p>
        <p><strong>Average Balance:</strong> ${StrawCoinUtils.formatNumber(stats.average_balance)}</p>
        <p><strong>Median Balance:</strong> ${StrawCoinUtils.formatNumber(stats.median_balance)}</p>
        <p><strong>Richest User Balance:</strong> ${StrawCoinUtils.formatNumber(stats.max_balance)}</p>
        <p><strong>Poorest User Balance:</strong> ${StrawCoinUtils.formatNumber(stats.min_balance)}</p>
    </div>
  `;

  StrawCoinUtils.createModal(modalContent);
}

function logQuantAction(type, message, level = "info") {
  const logEl = document.getElementById("quantLog");
  if (!logEl) return;

  const timestamp = new Date().toLocaleTimeString();
  const logClass = `log-${level}`;

  const logEntry = document.createElement("div");
  logEntry.className = `list-item`;
  logEntry.innerHTML = `
        <span class="text-xs opacity-70">[${timestamp}]</span>
        <span class="text-xs opacity-70">[${type}]</span>
        <span class="${level === 'error' ? 'text-danger' : level === 'success' ? 'text-success' : level === 'warning' ? 'text-warning' : 'text-secondary'}">${message}</span>
    `;

  logEl.appendChild(logEntry);

  // Keep only last 50 log entries
  const entries = logEl.querySelectorAll(".list-item");
  if (entries.length > 50) {
    entries[0].remove();
  }

  // Auto-scroll to bottom
  logEl.scrollTop = logEl.scrollHeight;
}

function showQuantStatus(message, type = "info") {
  StrawCoinUtils.showMessage(message, type, '#quantStatus');
}

async function toggleMarketStatus() {
  const marketStateSelect = document.getElementById("marketStateSelect");
  const newState = marketStateSelect.value;
  
  try {
    showQuantStatus("⚡ Updating market status...", "info");
    
    const data = await StrawCoinUtils.apiRequest("/api/quant/toggle-market", {
      method: "POST",
      body: JSON.stringify({
        state: newState
      }),
    });
    
    if (data) {
      // Update the display
      const marketStatusIndicator = document.getElementById("marketStatusIndicator");
      if (marketStatusIndicator) {
        marketStatusIndicator.textContent = data.market_status.status_text;
        marketStatusIndicator.style.color = data.market_status.status_color;
      }
      
      logQuantAction(
        "MARKET_CONTROL",
        `Market status changed to ${data.market_status.status_text}`,
        "manipulation"
      );
      
      showQuantStatus(
        `✅ ${data.message}`,
        "success"
      );
      
      // Update other market status displays if present
      updateMarketStatusDisplays(data.market_status);
    } else {
      throw new Error("Failed to update market status");
    }
  } catch (error) {
    console.error("Market toggle error:", error);
    logQuantAction(
      "ERROR",
      `Market toggle failed: ${error.message}`,
      "error"
    );
    showQuantStatus(`❌ Failed to update market status: ${error.message}`, "error");
  }
}

function updateMarketStatusDisplays(marketStatus) {
  // Update any other market status displays on the page
  const statusElements = document.querySelectorAll('[data-market-status]');
  statusElements.forEach(element => {
    element.textContent = marketStatus.status_text;
    element.style.color = marketStatus.status_color;
  });
}

// Enhanced error handling for The Quant's operations
window.addEventListener("error", function (event) {
  logQuantAction(
    "SYSTEM_ERROR",
    `JavaScript error: ${event.error?.message || "Unknown error"}`,
    "error",
  );
});

// Handle session management for The Quant
async function checkQuantSession() {
  const isAuthenticated = await StrawCoinUtils.checkSession();
  if (!isAuthenticated) {
    logQuantAction(
      "SESSION",
      "Session expired - redirecting to login",
      "error",
    );
  }
}

// Check session every 2 minutes
const sessionRefresh = StrawCoinUtils.createAutoRefresh(
  checkQuantSession,
  120000 // 2 minutes
);
sessionRefresh.start();

// Auto-refresh pending offers every 30 seconds
const offersRefresh = StrawCoinUtils.createAutoRefresh(
  loadPendingOffers,
  30000 // 30 seconds
);
offersRefresh.start();

// Pending Offers Functions
async function loadPendingOffers() {
  try {
    const container = document.getElementById("pendingOffersContainer");
    if (!container) return;
    
    const data = await StrawCoinUtils.apiRequest("/api/quant/pending-offers");
    
    if (data && data.offers) {
      displayPendingOffers(data.offers);
      
      // Log if there are new offers
      if (data.offers.length > 0) {
        logQuantAction(
          "OFFERS_CHECK",
          `Found ${data.offers.length} pending offers`,
          "info"
        );
      }
    }
  } catch (error) {
    console.error("Failed to load pending offers:", error);
    const container = document.getElementById("pendingOffersContainer");
    if (container) {
      container.innerHTML = '<div class="text-center opacity-70">Failed to load offers</div>';
    }
  }
}

function displayPendingOffers(offers) {
  const container = document.getElementById("pendingOffersContainer");
  if (!container) return;
  
  if (!offers || offers.length === 0) {
    container.innerHTML = '<div class="text-center opacity-70">No pending offers</div>';
    return;
  }
  
  const offersHtml = offers.map(offer => `
    <div class="pending-offer-card" data-offer-id="${offer.id}">
      <div class="pending-offer-header">
        <div class="pending-offer-info">
          <div class="pending-offer-sender">From: ${offer.sender}</div>
          <div class="pending-offer-recipient">To: ${offer.recipient}</div>
          <div class="text-xs opacity-70">${new Date(offer.timestamp).toLocaleString()}</div>
        </div>
        <div class="pending-offer-amount">
          ${StrawCoinUtils.formatNumber(offer.amount)} coins
        </div>
      </div>
      <div class="pending-offer-request">
        "${offer.request_text}"
      </div>
      <div class="pending-offer-actions">
        <button class="button button--success" onclick="approveOffer(${offer.id})">
          ✅ Approve
        </button>
        <button class="button button--danger" onclick="denyOffer(${offer.id})">
          ❌ Deny
        </button>
      </div>
    </div>
  `).join('');
  
  container.innerHTML = offersHtml;
}

async function approveOffer(offerId) {
  try {
    showQuantStatus("⚡ Approving offer...", "info");
    
    const data = await StrawCoinUtils.apiRequest("/api/quant/approve-offer", {
      method: "POST",
      body: JSON.stringify({ offer_id: offerId })
    });
    
    if (data) {
      logQuantAction(
        "OFFER_APPROVED",
        `Approved offer #${offerId}`,
        "success"
      );
      showQuantStatus(`✅ ${data.message}`, "success");
      
      // Remove the offer card with animation
      const offerCard = document.querySelector(`[data-offer-id="${offerId}"]`);
      if (offerCard) {
        offerCard.style.opacity = '0';
        offerCard.style.transform = 'scale(0.95)';
        setTimeout(() => {
          offerCard.remove();
          // Check if no offers left
          const container = document.getElementById("pendingOffersContainer");
          if (container && container.children.length === 0) {
            container.innerHTML = '<div class="text-center opacity-70">No pending offers</div>';
          }
        }, 300);
      }
    }
  } catch (error) {
    console.error("Failed to approve offer:", error);
    logQuantAction(
      "ERROR",
      `Failed to approve offer #${offerId}: ${error.message}`,
      "error"
    );
    showQuantStatus(`❌ Failed to approve offer: ${error.message}`, "error");
  }
}

async function denyOffer(offerId) {
  try {
    showQuantStatus("⚡ Denying offer...", "info");
    
    const data = await StrawCoinUtils.apiRequest("/api/quant/deny-offer", {
      method: "POST",
      body: JSON.stringify({ offer_id: offerId })
    });
    
    if (data) {
      logQuantAction(
        "OFFER_DENIED",
        `Denied offer #${offerId}`,
        "warning"
      );
      showQuantStatus(`✅ ${data.message}`, "success");
      
      // Remove the offer card with animation
      const offerCard = document.querySelector(`[data-offer-id="${offerId}"]`);
      if (offerCard) {
        offerCard.style.opacity = '0';
        offerCard.style.transform = 'scale(0.95)';
        setTimeout(() => {
          offerCard.remove();
          // Check if no offers left
          const container = document.getElementById("pendingOffersContainer");
          if (container && container.children.length === 0) {
            container.innerHTML = '<div class="text-center opacity-70">No pending offers</div>';
          }
        }, 300);
      }
    }
  } catch (error) {
    console.error("Failed to deny offer:", error);
    logQuantAction(
      "ERROR",
      `Failed to deny offer #${offerId}: ${error.message}`,
      "error"
    );
    showQuantStatus(`❌ Failed to deny offer: ${error.message}`, "error");
  }
}

// Make functions globally available
window.approveOffer = approveOffer;
window.denyOffer = denyOffer;
