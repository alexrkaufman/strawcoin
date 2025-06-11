// Straw Coin Registration Form Handler

document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("registrationForm");
  const usernameInput = document.getElementById("username");
  const registerBtn = document.getElementById("registerBtn");
  const errorMessage = document.getElementById("errorMessage");
  const loadingMessage = document.getElementById("loadingMessage");
  const successMessage = document.getElementById("successMessage");

  // Mobile-optimized input handling
  usernameInput.addEventListener("input", function () {
    this.value = this.value.replace(/[^a-zA-Z0-9_-]/g, "");
    if (this.value.length > 0) {
      registerBtn.style.opacity = "1";
    } else {
      registerBtn.style.opacity = "0.7";
    }
  });

  // Focus handling for mobile keyboards
  usernameInput.addEventListener("focus", function () {
    setTimeout(() => {
      this.scrollIntoView({ behavior: "smooth", block: "center" });
    }, 300);
  });

  // Touch-optimized button interactions
  StrawCoinUtils.addTouchOptimization(registerBtn);

  // Form submission handling
  form.addEventListener("submit", function (e) {
    e.preventDefault();

    const username = usernameInput.value.trim();
    const validation = StrawCoinUtils.validateUsername(username);
    
    if (!validation.isValid) {
      showError(validation.message);
      return;
    }

    registerUser(username);
  });

  function showError(message) {
    StrawCoinUtils.showError(message, '#errorMessage');
  }

  function showLoading(show) {
    loadingMessage.style.display = show ? "block" : "none";
    form.style.display = show ? "none" : "block";
  }

  function showSuccess(message) {
    StrawCoinUtils.showSuccess(message, '#successMessage');
    form.style.display = "none";
    loadingMessage.style.display = "none";
  }

  async function registerUser(username) {
    showLoading(true);

    try {
      const data = await StrawCoinUtils.apiRequest("/login", {
        method: "POST",
        body: JSON.stringify({ username: username }),
      });

      if (data && data.status === "authentication_successful") {
        // Success - show confirmation with timeout info before redirect
        const timeoutInfo = data.debug_mode
          ? `${data.session_timeout_seconds} seconds (debug mode)`
          : `${Math.floor(data.session_timeout_seconds / 60)} minutes`;
        showSuccess(
          `Welcome to Straw Coin, ${data.username}! You have ${StrawCoinUtils.formatNumber(data.balance)} coins.`,
        );
        setTimeout(() => {
          window.location.href = "/";
        }, 3000);
      } else {
        showLoading(false);
        showError(data.error || "Registration failed - please try again");
      }
    } catch (error) {
      showLoading(false);
      showError(error.message || "Network error - please check connection and retry");
      console.error("Registration error:", error);
    }
  }

  // Auto-focus username input on page load (mobile-friendly delay)
  setTimeout(() => {
    usernameInput.focus();
  }, 500);
});
