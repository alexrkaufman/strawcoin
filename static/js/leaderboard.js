// Straw Coin TV Leaderboard Display

let currentUsername = "";

document.addEventListener("DOMContentLoaded", function () {
  // Get current username from the page
  currentUsername = StrawCoinUtils.getCurrentUsername() || "";

  loadAllData();
  startAutoUpdate();
});

async function loadAllData() {
  try {
    // Load all data in parallel
    const [offersData, usersData, marketData] = await Promise.all([
      StrawCoinUtils.apiRequest("/api/leaderboard"),
      StrawCoinUtils.apiRequest("/api/users"),
      StrawCoinUtils.apiRequest("/api/market-stats")
    ]);

    // Display offers
    if (offersData && offersData.status === "success") {
      displayOffers(offersData.offers);
    }

    // Display rich and poor lists
    if (usersData && usersData.leaderboard) {
      displayRichestUsers(usersData.leaderboard);
      displayPoorestUsers(usersData.leaderboard);
    }

    // Update market stats
    if (marketData) {
      updateMarketStats(marketData);
    }

    // Update last refresh time
    const updateTimeEl = document.getElementById("updateTime");
    if (updateTimeEl) {
      updateTimeEl.textContent = `Last updated: ${new Date().toLocaleTimeString()}`;
    }
  } catch (error) {
    console.error("Error loading data:", error);
  }
}

function displayOffers(offers) {
  const container = document.getElementById("recentOffers");
  if (!container) return;

  if (!offers || offers.length === 0) {
    container.innerHTML = `
      <div class="text-center opacity-70">
        <p style="font-size: 1.5rem;">🎭 No approved offers yet!</p>
      </div>
    `;
    return;
  }

  // Display only the 5 most recent offers for TV
  const recentOffers = offers.slice(0, 5);
  const offersHtml = recentOffers.map((offer, index) => {
    const timestamp = new Date(offer.timestamp);
    const timeAgo = getTimeAgo(timestamp);

    return `
      <div class="tv-offer-card" style="animation-delay: ${index * 0.1}s">
        <div class="tv-offer-header">
          <div class="tv-offer-users">
            <span class="tv-offer-sender">${offer.sender}</span>
            <span>→</span>
            <span class="tv-offer-recipient">${offer.recipient}</span>
          </div>
          <div class="tv-offer-amount">
            ${StrawCoinUtils.formatNumber(offer.amount)}
          </div>
        </div>
        <div class="tv-offer-request">
          "${offer.request_text}"
        </div>
      </div>
    `;
  }).join('');

  container.innerHTML = offersHtml;
}

function displayRichestUsers(users) {
  const container = document.getElementById("richestUsers");
  if (!container || !users) return;

  // Get top 5 richest users
  const richest = users.slice(0, 5);
  const richestHtml = richest.map((user, index) => {
    const medals = ["🥇", "🥈", "🥉", "🏅", "💰"];
    return `
      <div class="tv-ranking-item tv-ranking-item--rich">
        <span class="tv-ranking-position">${medals[index]}</span>
        <span class="tv-ranking-user">${user.username}</span>
        <span class="tv-ranking-balance tv-ranking-balance--rich">
          ${StrawCoinUtils.formatNumber(user.coin_balance)}
        </span>
      </div>
    `;
  }).join('');

  container.innerHTML = richestHtml;
}

function displayPoorestUsers(users) {
  const container = document.getElementById("poorestUsers");
  if (!container || !users) return;

  // Get bottom 5 poorest users (reverse sort)
  const poorest = [...users].sort((a, b) => a.coin_balance - b.coin_balance).slice(0, 5);
  const poorestHtml = poorest.map((user, index) => {
    const emojis = ["😢", "😭", "🥺", "😔", "💸"];
    return `
      <div class="tv-ranking-item tv-ranking-item--poor">
        <span class="tv-ranking-position">${emojis[index]}</span>
        <span class="tv-ranking-user">${user.username}</span>
        <span class="tv-ranking-balance tv-ranking-balance--poor">
          ${StrawCoinUtils.formatNumber(user.coin_balance)}
        </span>
      </div>
    `;
  }).join('');

  container.innerHTML = poorestHtml;
}

function getTimeAgo(date) {
  const seconds = Math.floor((new Date() - date) / 1000);
  
  if (seconds < 60) return 'just now';
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes} minute${minutes !== 1 ? 's' : ''} ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours} hour${hours !== 1 ? 's' : ''} ago`;
  const days = Math.floor(hours / 24);
  return `${days} day${days !== 1 ? 's' : ''} ago`;
}

function updateMarketStats(data) {
  if (!data) return;

  // Update market cap
  const marketCapEl = document.getElementById("marketCap");
  if (marketCapEl) {
    marketCapEl.textContent = StrawCoinUtils.formatNumber(data.market_cap, "STRAW");
  }

  // Update volume
  const volumeEl = document.getElementById("volume24h");
  if (volumeEl) {
    volumeEl.textContent = StrawCoinUtils.formatNumber(data.total_volume, "STRAW");
  }

  // Update active traders
  const tradersEl = document.getElementById("activeTraders");
  if (tradersEl) {
    tradersEl.textContent = data.total_users;
  }
}

async function updateUserPosition() {
  try {
    const data = await StrawCoinUtils.apiRequest("/api/leaderboard");
    const positionElement = document.getElementById("userPosition");
    
    if (positionElement && data && data.status === "success") {
      const usersData = await StrawCoinUtils.apiRequest("/api/users");
      if (usersData && usersData.leaderboard) {
        const userPosition = usersData.leaderboard.findIndex(
          (user) => user.username === currentUsername
        ) + 1;

        if (userPosition > 0) {
          let positionText = `#${userPosition}`;
          if (userPosition === 1) positionText += " 🥇";
          else if (userPosition === 2) positionText += " 🥈";
          else if (userPosition === 3) positionText += " 🥉";
          positionElement.textContent = positionText;
        } else {
          positionElement.textContent = "Unranked";
        }
      }
    }
  } catch (error) {
    console.log("Position update failed:", error);
  }
}

function startAutoUpdate() {
  // Update everything every 10 seconds for TV display
  const tvRefresh = StrawCoinUtils.createAutoRefresh(
    loadAllData,
    10000 // 10 seconds
  );
  tvRefresh.start();
}

// Export for global use
window.StrawCoinLeaderboard = {
  loadAllData,
  displayOffers,
  displayRichestUsers,
  displayPoorestUsers,
};
