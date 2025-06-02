// Straw Coin Mobile Activity Enhancement
// Simple mobile optimization for session timeout

(function() {
    let isActive = true;
    
    function initMobileActivity() {
        // Add mobile-specific events
        const mobileEvents = ['touchstart', 'touchmove', 'touchend', 'touchcancel'];
        
        mobileEvents.forEach(event => {
            document.addEventListener(event, handleMobileActivity, { passive: true });
        });

        // Handle app state changes
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                handleMobileActivity();
            }
        });
        
        window.addEventListener('focus', handleMobileActivity);
        window.addEventListener('pageshow', handleMobileActivity);
    }

    function handleMobileActivity() {
        if (!isActive) return;
        
        // Throttle for performance
        isActive = false;
        setTimeout(() => { isActive = true; }, 500);

        // Trigger activity event for session timer
        document.dispatchEvent(new Event('touchactivity'));
    }

    // Initialize when ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initMobileActivity);
    } else {
        initMobileActivity();
    }
})();