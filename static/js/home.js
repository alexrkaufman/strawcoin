// Straw Coin Home Page JavaScript

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
            validRecipients.push(option.value);
        });
    }

    // Get current username from the page
    const currentUsername = window.currentUsername || '';

    // Clean input validation without spoiling the surprises

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
                        this.style.borderColor = '#e74c3c'; // Red for invalid
                    }
                }
            }
        });

        // Clear validation styling on focus
        recipientInput.addEventListener('focus', function() {
            this.style.borderColor = '';
        });
    }

    // Quick send button functionality
    quickSendButtons.forEach(button => {
        button.addEventListener('click', function() {
            const amount = parseInt(this.dataset.amount);
            const recipient = this.dataset.recipient;

            if (amountInput && recipientInput) {
                amountInput.value = amount;
                recipientInput.value = recipient;

                // Trigger validation
                recipientInput.dispatchEvent(new Event('input'));

                // Visual feedback for clicked button
                quickSendButtons.forEach(btn => btn.style.background = 'rgba(255,255,255,0.2)');
                this.style.background = 'rgba(46, 204, 113, 0.3)';
            }
        });
    });

    // Form submission
    if (sendForm) {
        sendForm.addEventListener('submit', async function(e) {
            e.preventDefault();

            const recipient = recipientInput.value.trim();
            const amount = parseInt(amountInput.value);

            if (!recipient || !amount || amount <= 0) {
                showStatus('Please enter a valid recipient and amount', 'error');
                return;
            }

            // Basic validation - let the API handle special cases

            const submitButton = sendForm.querySelector('button[type="submit"]');
            const originalText = submitButton.textContent;

            try {
                // Disable form and show loading
                submitButton.textContent = '🔄 Sending...';
                submitButton.disabled = true;

                // Find exact recipient match (case-insensitive)
                const trimmedRecipient = recipient.toLowerCase();
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

                // Handle redirects for violations
                if (data.redirect) {
                    if (data.status === 'insider_trading_violation') {
                        // Show brief warning before redirect
                        showStatus('🚨 INSIDER TRADING DETECTED! Redirecting to violation notice...', 'error');
                        setTimeout(() => {
                            window.location.href = data.redirect;
                        }, 2000);
                    } else if (data.status === 'quant_independence_violation') {
                        // Show brief warning before redirect
                        showStatus('⚖️ QUANT INDEPENDENCE VIOLATION! Redirecting to notice...', 'error');
                        setTimeout(() => {
                            window.location.href = data.redirect;
                        }, 2000);
                    } else {
                        // Other redirects
                        window.location.href = data.redirect;
                    }
                    return;
                }

                if (response.ok && data.status === 'success') {
                    showStatus(`🎉 Successfully sent ${amount.toLocaleString()} coins to ${recipient}!`, 'success');

                    // Reset form
                    sendForm.reset();
                    quickSendButtons.forEach(btn => btn.style.background = 'rgba(255,255,255,0.2)');

                    // Refresh page after a short delay to update balances
                    setTimeout(() => {
                        window.location.reload();
                    }, 2000);
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
        statusDiv.style.borderRadius = '8px';
        statusDiv.style.marginTop = '15px';
        statusDiv.style.fontWeight = 'bold';

        // Auto-hide success messages
        if (type === 'success') {
            setTimeout(() => {
                statusDiv.style.display = 'none';
            }, 5000);
        }
    }

    // Live balance updates (placeholder for future WebSocket implementation)
    function startLiveUpdates() {
        setInterval(() => {
            // Could implement WebSocket or polling here for live balance updates
            // For now, just update the timestamp if there's a balance display
            const balanceTimestamp = document.querySelector('.balance-timestamp');
            if (balanceTimestamp) {
                balanceTimestamp.textContent = `Updated: ${new Date().toLocaleTimeString()}`;
            }
        }, 30000); // Every 30 seconds
    }

    // Initialize live updates
    startLiveUpdates();

    // Add current username to global scope for validation
    window.currentUsername = currentUsername;
});