// Straw Coin Home Page Functionality

document.addEventListener("DOMContentLoaded", function () {
  const sendForm = document.getElementById("sendCoinsForm");
  const quickSendButtons = document.querySelectorAll(".quickSend");
  const statusDiv = document.getElementById("transferStatus");
  const amountInput = document.getElementById("amount");
  const recipientInput = document.getElementById("recipient");
  const recipientList = document.getElementById("recipientList");
  const currentUsername = StrawCoinUtils.getCurrentUsername();

  // Get list of valid recipients for validation
  const validRecipients = [];
  if (recipientList) {
    const options = recipientList.querySelectorAll("option");
    options.forEach((option) => {
      if (option.value) {
        validRecipients.push(option.value);
      }
    });
  }

  // Add recipient input validation and feedback
  if (recipientInput) {
    recipientInput.addEventListener("input", function () {
      const value = this.value.trim();

      // Remove any special styling first
      this.style.borderColor = "";

      if (value.length > 0) {
        // Check if the entered value matches a valid recipient
        const isValid = validRecipients.some(
          (recipient) => recipient.toLowerCase() === value.toLowerCase(),
        );

        if (isValid) {
          this.style.borderColor = "#2ecc71"; // Green for valid
        } else {
          // Check if it's a partial match
          const partialMatch = validRecipients.some((recipient) =>
            recipient.toLowerCase().startsWith(value.toLowerCase()),
          );

          if (partialMatch) {
            this.style.borderColor = "#f39c12"; // Orange for partial match
          } else {
            this.style.borderColor = "#e74c3c"; // Red for no match
          }
        }
      }
    });

    // Clear validation styling on focus
    recipientInput.addEventListener("focus", function () {
      this.style.borderColor = "#3498db";
    });
  }

  // Quick send button functionality
  quickSendButtons.forEach((button) => {
    button.addEventListener("click", function () {
      const amount = this.getAttribute("data-amount");
      amountInput.value = amount;

      // Highlight the selected amount
      quickSendButtons.forEach(
        (btn) => (btn.style.background = "rgba(255,255,255,0.2)"),
      );
      this.style.background = "rgba(255,255,255,0.4)";
    });
  });

  // Form submission
  if (sendForm) {
    sendForm.addEventListener("submit", async function (e) {
      e.preventDefault();

      const recipient = recipientInput.value;
      const amount = parseInt(amountInput.value);

      if (!recipient || !amount || amount <= 0) {
        showStatus("Please enter a recipient and a valid amount", "error");
        return;
      }

      // Validate that the recipient exists in the list (case-insensitive)
      const trimmedRecipient = recipient.trim();
      const isValidRecipient = validRecipients.some(
        (validRecipient) =>
          validRecipient.toLowerCase() === trimmedRecipient.toLowerCase(),
      );

      if (!isValidRecipient) {
        showStatus("Please enter a valid recipient username", "error");
        recipientInput.style.borderColor = "#e74c3c";
        return;
      }

      // Get current balance from the page
      const balanceElement = document.querySelector(".balance-amount");
      const currentBalance = balanceElement
        ? parseInt(balanceElement.textContent.replace(/[^0-9]/g, ""))
        : 0;

      if (amount > currentBalance) {
        showStatus(
          "Insufficient funds! You only have " +
            currentBalance.toLocaleString() +
            " coins",
          "error",
        );
        return;
      }

      try {
        // Disable form during request
        const submitButton = sendForm.querySelector('button[type="submit"]');
        const originalText = submitButton.textContent;
        submitButton.textContent = "🚀 Sending...";
        submitButton.disabled = true;



        // Use the exact case from the valid recipients list
        const exactRecipient =
          validRecipients.find(
            (validRecipient) =>
              validRecipient.toLowerCase() === trimmedRecipient.toLowerCase(),
          ) || trimmedRecipient;

        const data = await StrawCoinUtils.apiRequest("/api/transfer", {
          method: "POST",
          body: JSON.stringify({
            sender: currentUsername,
            recipient: exactRecipient,
            amount: amount,
          }),
        });

        if (data && data.status === "success") {
          StrawCoinUtils.showSuccess(
            `🎉 Successfully sent ${StrawCoinUtils.formatNumber(amount)} coins to ${recipient}!`,
            '#transferStatus'
          );

          // Reset form
          sendForm.reset();
          quickSendButtons.forEach(
            (btn) => (btn.style.background = "rgba(255,255,255,0.2)"),
          );

          // Refresh page after a short delay to update balances
          setTimeout(() => {
            window.location.reload();
          }, 2000);
        } else {
          StrawCoinUtils.showError(`Error: ${data.message || "Transfer failed"}`, '#transferStatus');
        }

        // Re-enable form
        submitButton.textContent = originalText;
        submitButton.disabled = false;
      } catch (error) {
        StrawCoinUtils.showError(error.message || "Network error. Please try again.", '#transferStatus');
        console.error("Transfer error:", error);

        // Re-enable form
        const submitButton = sendForm.querySelector('button[type="submit"]');
        submitButton.textContent = "🚀 Send Coins";
        submitButton.disabled = false;
      }
    });
  }

  function showStatus(message, type) {
    StrawCoinUtils.showMessage(message, type, '#transferStatus');
  }

  // Initialize tooltips for performer status
  const performerCards = document.querySelectorAll(".performer-status-card");
  performerCards.forEach((card) => {
    card.addEventListener("mouseenter", function () {
      this.style.transform = "scale(1.02)";
    });

    card.addEventListener("mouseleave", function () {
      this.style.transform = "scale(1)";
    });
  });

  // Auto-refresh market stats
  const marketRefresh = StrawCoinUtils.createAutoRefresh(
    updateMarketStats,
    StrawCoinUtils.REFRESH_INTERVALS.marketStats
  );
  marketRefresh.start();

  async function updateMarketStats() {
    try {
      const data = await StrawCoinUtils.apiRequest("/api/market-stats");
      if (data) {
        StrawCoinUtils.updateMarketStats(data);
      }
    } catch (error) {
      console.log("Market stats update failed:", error);
    }
  }
});
