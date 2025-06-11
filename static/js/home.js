// Straw Coin Home Page Functionality

document.addEventListener("DOMContentLoaded", function () {
  const sendForm = document.getElementById("sendCoinsForm");
  const quickSendButtons = document.querySelectorAll(".quickSend");
  const statusDiv = document.getElementById("transferStatus");
  const amountInput = document.getElementById("amount");
  const recipientInput = document.getElementById("recipient");
  const recipientList = document.getElementById("recipientList");
  const currentUsername = StrawCoinUtils.getCurrentUsername();
  const requestText = document.getElementById("requestText");
  const makeOfferBtn = document.getElementById("makeOfferBtn");
  const sendTipBtn = document.getElementById("sendTipBtn");

  // Get list of valid recipients and their performer status
  const recipientData = {};
  if (recipientList) {
    const options = recipientList.querySelectorAll("option");
    options.forEach((option) => {
      if (option.value) {
        const performerAttr = option.getAttribute("data-performer");
        recipientData[option.value.toUpperCase()] = {
          username: option.value,
          isPerformer: performerAttr === "true"
        };
      }
    });
  }

  // Handle Make Offer button
  if (makeOfferBtn) {
    makeOfferBtn.addEventListener("click", function() {
      handleSubmit("offer");
    });
  }

  // Handle Send Tip button
  if (sendTipBtn) {
    sendTipBtn.addEventListener("click", function() {
      handleSubmit("tip");
    });
  }

  // Add recipient input validation and feedback
  if (recipientInput) {
    recipientInput.addEventListener("input", function () {
      const value = this.value.trim().toUpperCase();

      // Remove any special styling first
      this.style.borderColor = "";

      // Check if recipient is a performer and update offer button
      if (recipientData[value]) {
        const userData = recipientData[value];
        const isPerformer = userData.isPerformer;
        
        if (isPerformer) {
          makeOfferBtn.disabled = false;
          makeOfferBtn.classList.remove("button--disabled");
          makeOfferBtn.title = "";
        } else {
          makeOfferBtn.disabled = true;
          makeOfferBtn.classList.add("button--disabled");
          makeOfferBtn.title = "Offers can only be made to performers";
        }
        
        this.style.borderColor = "#2ecc71"; // Green for valid
      } else if (value.length === 0) {
        // Reset when input is empty
        makeOfferBtn.disabled = true;
        makeOfferBtn.classList.add("button--disabled");
        makeOfferBtn.title = "Select a performer to make an offer";
      } else {
        // Check if it's a partial match
        const partialMatch = Object.keys(recipientData).some(key =>
          key.startsWith(value)
        );

        if (partialMatch) {
          this.style.borderColor = "#f39c12"; // Orange for partial match
        } else if (value.length > 0) {
          this.style.borderColor = "#e74c3c"; // Red for no match
        }
        
        // Disable offer button if no valid recipient
        makeOfferBtn.disabled = true;
        makeOfferBtn.classList.add("button--disabled");
        makeOfferBtn.title = "Select a valid performer to make an offer";
      }
    });

    // Clear validation styling on focus
    recipientInput.addEventListener("focus", function () {
      this.style.borderColor = "#3498db";
    });
    
    // Also check on blur to update button state
    recipientInput.addEventListener("blur", function () {
      const value = this.value.trim().toUpperCase();
      if (recipientData[value]) {
        const isPerformer = recipientData[value].isPerformer;
        if (isPerformer) {
          makeOfferBtn.disabled = false;
          makeOfferBtn.classList.remove("button--disabled");
          makeOfferBtn.title = "";
        } else {
          makeOfferBtn.disabled = true;
          makeOfferBtn.classList.add("button--disabled");
          makeOfferBtn.title = "Offers can only be made to performers";
        }
      }
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

  // Handle form submission
  async function handleSubmit(transactionType) {
    const recipient = recipientInput.value;
    const amount = parseInt(amountInput.value);
    const request = requestText.value.trim();

    if (!recipient || !amount || amount <= 0) {
      showStatus("Please enter a recipient and a valid amount", "error");
      return;
    }

    if (transactionType === "offer" && (!request || request.length === 0)) {
      showStatus("Please enter what you'd like the performer to do", "error");
      requestText.focus();
      return;
    }

      // Validate that the recipient exists in the list
      const trimmedRecipient = recipient.trim().toUpperCase();
      const recipientInfo = recipientData[trimmedRecipient];

      if (!recipientInfo) {
        showStatus("Please enter a valid recipient username", "error");
        recipientInput.style.borderColor = "#e74c3c";
        return;
      }

      // For offers, check if recipient is a performer
      if (transactionType === "offer" && !recipientInfo.isPerformer) {
        showStatus("Offers can only be made to performers", "error");
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
      // Disable buttons during request
      makeOfferBtn.disabled = true;
      sendTipBtn.disabled = true;
      
      const activeButton = transactionType === "offer" ? makeOfferBtn : sendTipBtn;
      const originalText = activeButton.textContent;
      activeButton.textContent = "🚀 Sending...";

        // Use the exact case from the recipient data
        const exactRecipient = recipientInfo.username;

        const requestBody = {
          sender: currentUsername,
          recipient: exactRecipient,
          amount: amount,
          transaction_type: transactionType
        };

        if (transactionType === "offer" && request) {
          requestBody.request_text = request;
        }

        const data = await StrawCoinUtils.apiRequest("/api/transfer", {
          method: "POST",
          body: JSON.stringify(requestBody),
        });

        // If data is null, a redirect happened (e.g., self-dealing warning)
        if (data === null) {
          // Redirect was handled by apiRequest, nothing more to do
          return;
        }

        if (data && (data.status === "success" || data.status === "offer_pending")) {
          if (data.status === "offer_pending") {
            StrawCoinUtils.showSuccess(
              `🎭 Offer sent! ${StrawCoinUtils.formatNumber(amount)} coins will be transferred if The Chancellor approves your request.`,
              "#transferStatus",
            );
          } else {
            StrawCoinUtils.showSuccess(
              `💰 Successfully tipped ${StrawCoinUtils.formatNumber(amount)} coins to ${recipient}!`,
              "#transferStatus",
            );
          }

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
          StrawCoinUtils.showError(
            `Error: ${data.message || "Transfer failed"}`,
            "#transferStatus",
          );
        }

        // Re-enable buttons
        activeButton.textContent = originalText;
        makeOfferBtn.disabled = false;
        sendTipBtn.disabled = false;
      } catch (error) {
        StrawCoinUtils.showError(
          error.message || "Network error. Please try again.",
          "#transferStatus",
        );
        console.error("Transfer error:", error);

        // Re-enable form
        const submitButton = sendForm.querySelector('button[type="submit"]');
        submitButton.textContent = "🚀 Send Coins";
      activeButton.textContent = originalText;
      makeOfferBtn.disabled = false;
      sendTipBtn.disabled = false;
    }
  }

  function showStatus(message, type) {
    StrawCoinUtils.showMessage(message, type, "#transferStatus");
  }

  // Initial state - disable offer button until a performer is selected
  if (makeOfferBtn) {
    makeOfferBtn.disabled = true;
    makeOfferBtn.classList.add("button--disabled");
    makeOfferBtn.title = "Select a performer to make an offer";
  }

  // Auto-refresh market stats
  const marketRefresh = StrawCoinUtils.createAutoRefresh(
    updateMarketStats,
    StrawCoinUtils.REFRESH_INTERVALS.marketStats,
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
