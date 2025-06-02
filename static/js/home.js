// Straw Coin Home Page Functionality

document.addEventListener('DOMContentLoaded', function() {
    const sendForm = document.getElementById('sendCoinsForm');
    const quickSendButtons = document.querySelectorAll('.quickSend');
    const statusDiv = document.getElementById('transferStatus');
    const amountInput = document.getElementById('amount');
    const recipientInput = document.getElementById('recipient');
    const recipientList = document.getElementById('recipientList');

    // Get list of valid recipients for validation
    const validRecipients = [];
    if (recipientList) {
        const options = recipientList.querySelectorAll('option');
        options.forEach(option => {
            if (option.value) {
                validRecipients.push(option.value);
            }
        });
    }

    // Add recipient input validation and feedback
    if (recipientInput) {
        recipientInput.addEventListener('input', function() {
            const value = this.value.trim();
            
            // Remove any special styling first
            this.style.borderColor = '';
            
            if (value.length > 0) {
                // Check if the entered value matches a valid recipient
                const isValid = validRecipients.some(recipient => 
                    recipient.toLowerCase() === value.toLowerCase()
                );
                
                if (isValid) {
                    this.style.borderColor = '#2ecc71'; // Green for valid
                } else {
                    // Check if it's a partial match
                    const partialMatch = validRecipients.some(recipient => 
                        recipient.toLowerCase().startsWith(value.toLowerCase())
                    );
                    
                    if (partialMatch) {
                        this.style.borderColor = '#f39c12'; // Orange for partial match
                    } else {
                        this.style.borderColor = '#e74c3c'; // Red for no match
                    }
                }
            }
        });

        // Clear validation styling on focus
        recipientInput.addEventListener('focus', function() {
            this.style.borderColor = '#3498db';
        });
    }

    // Quick send button functionality
    quickSendButtons.forEach(button => {
        button.addEventListener('click', function() {
            const amount = this.getAttribute('data-amount');
            amountInput.value = amount;

            // Highlight the selected amount
            quickSendButtons.forEach(btn => btn.style.background = 'rgba(255,255,255,0.2)');
            this.style.background = 'rgba(255,255,255,0.4)';
        });
    });

    // Form submission
    if (sendForm) {
        sendForm.addEventListener('submit', async function(e) {
            e.preventDefault();

            const recipient = recipientInput.value;
            const amount = parseInt(amountInput.value);

            if (!recipient || !amount || amount <= 0) {
                showStatus('Please enter a recipient and a valid amount', 'error');
                return;
            }

            // Validate that the recipient exists in the list (case-insensitive)
            const trimmedRecipient = recipient.trim();
            const isValidRecipient = validRecipients.some(validRecipient => 
                validRecipient.toLowerCase() === trimmedRecipient.toLowerCase()
            );

            if (!isValidRecipient) {
                showStatus('Please enter a valid recipient username', 'error');
                recipientInput.style.borderColor = '#e74c3c';
                return;
            }

            // Get current balance from the page
            const balanceElement = document.querySelector('.balance-amount');
            const currentBalance = balanceElement ? 
                parseInt(balanceElement.textContent.replace(/[^0-9]/g, '')) : 0;

            if (amount > currentBalance) {
                showStatus('Insufficient funds! You only have ' + currentBalance.toLocaleString() + ' coins', 'error');
                return;
            }

            try {
                // Disable form during request
                const submitButton = sendForm.querySelector('button[type="submit"]');
                const originalText = submitButton.textContent;
                submitButton.textContent = '🚀 Sending...';
                submitButton.disabled = true;

                // Get current username from the page
                const usernameElement = document.querySelector('[data-username]');
                const currentUsername = usernameElement ? 
                    usernameElement.getAttribute('data-username') : 
                    window.currentUsername;

                // Use the exact case from the valid recipients list
                const exactRecipient = validRecipients.find(validRecipient =>
                    validRecipient.toLowerCase() === trimmedRecipient.toLowerCase()
                ) || trimmedRecipient;

                const response = await fetch('/api/transfer', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        sender: currentUsername,
                        recipient: exactRecipient,
                        amount: amount
                    })
                });

                const data = await response.json();

                if (response.ok && data.status === 'success') {
                    showStatus(`🎉 Successfully sent ${amount.toLocaleString()} coins to ${recipient}!`, 'success');

                    // Reset form
                    sendForm.reset();
                    quickSendButtons.forEach(btn => btn.style.background = 'rgba(255,255,255,0.2)');

                    // Refresh page after a short delay to update balances
                    setTimeout(() => {
                        window.location.reload();
                    }, 2000);
                } else if (data.redirect) {
                    // Handle redirects (quant independence, insider trading warnings)
                    window.location.href = data.redirect;
                    return;
                } else {
                    showStatus(`Error: ${data.message || 'Transfer failed'}`, 'error');
                }

                // Re-enable form
                submitButton.textContent = originalText;
                submitButton.disabled = false;

            } catch (error) {
                showStatus('Network error. Please try again.', 'error');
                console.error('Transfer error:', error);

                // Re-enable form
                const submitButton = sendForm.querySelector('button[type="submit"]');
                submitButton.textContent = '🚀 Send Coins';
                submitButton.disabled = false;
            }
        });
    }

    function showStatus(message, type) {
        if (!statusDiv) return;

        statusDiv.style.display = 'block';
        statusDiv.innerHTML = message;

        if (type === 'success') {
            statusDiv.style.background = 'rgba(46, 204, 113, 0.9)';
            statusDiv.style.color = 'white';
        } else {
            statusDiv.style.background = 'rgba(231, 76, 60, 0.9)';
            statusDiv.style.color = 'white';
        }

        statusDiv.style.padding = '15px';
        statusDiv.style.borderRadius = '10px';
        statusDiv.style.margin = '20px 0';
        statusDiv.style.textAlign = 'center';
        statusDiv.style.fontWeight = 'bold';

        // Auto-hide after 5 seconds
        setTimeout(() => {
            statusDiv.style.display = 'none';
        }, 5000);
    }

    // Add hover effects to buttons
    const allButtons = document.querySelectorAll('button');
    allButtons.forEach(button => {
        button.addEventListener('mouseenter', function() {
            if (!this.disabled) {
                this.style.transform = 'scale(1.05)';
            }
        });

        button.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1)';
        });
    });

    // Initialize tooltips for performer status
    const performerCards = document.querySelectorAll('.performer-status-card');
    performerCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.02)';
        });

        card.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1)';
        });
    });

    // Auto-refresh market stats every 30 seconds
    setInterval(() => {
        updateMarketStats();
    }, 30000);

    async function updateMarketStats() {
        try {
            const response = await fetch('/api/market-stats');
            if (response.ok) {
                const data = await response.json();
                
                // Update market cap
                const marketCapElement = document.querySelector('[data-stat="market-cap"]');
                if (marketCapElement) {
                    marketCapElement.textContent = data.market_cap.toLocaleString();
                }

                // Update user count
                const userCountElement = document.querySelector('[data-stat="user-count"]');
                if (userCountElement) {
                    userCountElement.textContent = data.total_users;
                }

                // Update transaction volume
                const volumeElement = document.querySelector('[data-stat="volume"]');
                if (volumeElement) {
                    volumeElement.textContent = data.total_volume.toLocaleString();
                }
            }
        } catch (error) {
            console.log('Market stats update failed:', error);
        }
    }
});