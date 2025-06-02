// Straw Coin Session Expired Page JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Auto-redirect countdown for mobile UX
    let countdown = 10;
    const countdownElement = document.getElementById('countdown');
    const redirectButton = document.getElementById('redirectButton');

    function updateCountdown() {
        if (countdownElement) {
            countdownElement.textContent = countdown;
        }
        
        countdown--;
        
        if (countdown < 0) {
            window.location.href = '/register';
        }
    }

    // Start countdown
    const countdownInterval = setInterval(updateCountdown, 1000);

    // Handle manual redirect
    if (redirectButton) {
        redirectButton.addEventListener('click', function(e) {
            e.preventDefault();
            clearInterval(countdownInterval);
            window.location.href = '/register';
        });
    }

    // Mobile touch optimization
    document.addEventListener('touchstart', function() {
        // Clear any existing session data
        if (typeof(Storage) !== "undefined") {
            localStorage.clear();
            sessionStorage.clear();
        }
    });

    // Clear any cached session data
    if (typeof(Storage) !== "undefined") {
        localStorage.removeItem('straw_coin_session');
        sessionStorage.clear();
    }
});