// Straw Coin Session Management
// Mobile-Optimized Session Management for The Short Straw Trading Platform

(function() {
    let sessionCheckInterval;
    let activityEvents = ['touchstart', 'touchmove', 'touchend', 'scroll', 'click', 'keypress'];
    let isActive = true;
    
    // Mobile-specific session monitoring
    function initSessionTracking() {
        // Check if user is authenticated
        fetch('/session-status')
            .then(response => {
                if (response.status === 401) {
                    // Not authenticated - redirect to registration
                    if (window.location.pathname !== '/register' && 
                        window.location.pathname !== '/session-expired') {
                        window.location.href = '/register';
                    }
                    return;
                }
                return response.json();
            })
            .then(data => {
                if (data && data.authenticated) {
                    startSessionMonitoring();
                    setupActivityTracking();
                }
            })
            .catch(error => {
                console.error('Session check failed:', error);
            });
    }

    function startSessionMonitoring() {
        // Check session status every 5 seconds for mobile optimization (frequent in debug mode)
        sessionCheckInterval = setInterval(() => {
            fetch('/session-status')
                .then(response => {
                    if (response.status === 401) {
                        clearInterval(sessionCheckInterval);
                        window.location.href = '/session-expired';
                        return null;
                    }
                    return response.json();
                })
                .then(data => {
                    if (data && data.time_remaining_seconds <= 10) {
                        // Show warning for last 10 seconds (works for both debug and production)
                        showSessionWarning(data.time_remaining_seconds);
                    }
                    if (data && data.time_remaining_seconds <= 0) {
                        // Force logout if time is up
                        clearInterval(sessionCheckInterval);
                        window.location.href = '/session-expired';
                    }
                })
                .catch(error => {
                    console.error('Session monitoring error:', error);
                });
        }, 5000);
    }

    function setupActivityTracking() {
        // Track mobile-specific events to maintain session
        activityEvents.forEach(event => {
            document.addEventListener(event, handleActivity, { passive: true });
        });

        // Mobile-specific: track page visibility changes
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                handleActivity();
            }
        });

        // Handle mobile app state changes
        window.addEventListener('focus', handleActivity);
        window.addEventListener('pageshow', handleActivity);
    }

    function handleActivity() {
        if (!isActive) return;
        
        // Throttle activity updates for mobile performance
        isActive = false;
        setTimeout(() => { isActive = true; }, 1000);

        // Update session activity using dedicated endpoint
        fetch('/update-activity', { 
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        })
            .then(response => {
                if (response.status === 401) {
                    window.location.href = '/session-expired';
                }
            })
            .catch(error => {
                console.error('Activity update failed:', error);
            });
    }

    function showSessionWarning(seconds) {
        // Mobile-friendly session warning
        let existingWarning = document.getElementById('session-warning');
        if (existingWarning) return;

        let warning = document.createElement('div');
        warning.id = 'session-warning';
        warning.className = 'session-warning';
        warning.innerHTML = `⚠️ Session expires in ${seconds}s - Tap to extend!`;
        
        warning.addEventListener('click', () => {
            handleActivity();
            warning.remove();
        });

        warning.addEventListener('touchstart', () => {
            handleActivity();
            warning.remove();
        });

        document.body.appendChild(warning);

        setTimeout(() => {
            if (warning.parentNode) {
                warning.remove();
            }
        }, 5000);
    }

    // Initialize session tracking when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initSessionTracking);
    } else {
        initSessionTracking();
    }

    // Cleanup on page unload
    window.addEventListener('beforeunload', () => {
        if (sessionCheckInterval) {
            clearInterval(sessionCheckInterval);
        }
    });

    // Export functions for global use
    window.StrawCoinSession = {
        handleActivity,
        showSessionWarning
    };
})();