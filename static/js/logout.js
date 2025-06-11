// Straw Coin Logout Handler
// Handles user logout functionality with proper session cleanup

function handleLogout() {
  // Disable the logout button to prevent multiple clicks
  const logoutBtn = document.querySelector(".logout-btn");
  if (logoutBtn) {
    logoutBtn.disabled = true;
    logoutBtn.innerHTML =
      '<span class="logout-icon">⏳</span><span class="logout-text">Logging out...</span>';
  }

  // Send logout request
  fetch("/logout", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "same-origin",
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.status === "logout_successful") {
        // Show success message briefly
        if (logoutBtn) {
          logoutBtn.innerHTML =
            '<span class="logout-icon">✓</span><span class="logout-text">Logged out!</span>';
        }

        // Redirect to registration page after a short delay
        setTimeout(() => {
          window.location.href = "/register";
        }, 500);
      } else {
        // Handle unexpected response
        console.error("Logout failed:", data);
        window.location.href = "/register";
      }
    })
    .catch((error) => {
      console.error("Logout error:", error);
      // Even on error, redirect to registration page
      window.location.href = "/register";
    });
}

// Add event listener to logout button when DOM is ready
document.addEventListener("DOMContentLoaded", function () {
  const logoutBtn = document.querySelector(".logout-btn");
  if (logoutBtn) {
    // Remove any inline onclick handler and use addEventListener
    logoutBtn.onclick = null;
    logoutBtn.addEventListener("click", handleLogout);
  }
});
