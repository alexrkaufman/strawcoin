// Straw Coin Shared Utilities
// Common functionality used across multiple pages

const StrawCoinUtils = (function() {
    'use strict';

    // API Configuration
    const API_CONFIG = {
        headers: {
            'Content-Type': 'application/json'
        },
        credentials: 'same-origin'
    };

    // Message type configurations
    const MESSAGE_TYPES = {
        success: {
            background: 'rgba(46, 204, 113, 0.9)',
            color: 'white',
            duration: 5000
        },
        error: {
            background: 'rgba(231, 76, 60, 0.9)',
            color: 'white',
            duration: 7000
        },
        info: {
            background: 'rgba(52, 152, 219, 0.9)',
            color: 'white',
            duration: 5000
        },
        warning: {
            background: 'rgba(241, 196, 15, 0.9)',
            color: 'white',
            duration: 5000
        }
    };

    // Refresh intervals (in milliseconds)
    const REFRESH_INTERVALS = {
        marketStats: 30000,      // 30 seconds
        chartData: 30000,        // 30 seconds
        liveIndicators: 5000     // 5 seconds
    };

    /**
     * Display a status message with consistent styling
     * @param {string} message - The message to display
     * @param {string} type - The message type (success, error, info, warning)
     * @param {HTMLElement|string} container - The container element or selector
     * @param {number} duration - Optional custom duration (ms)
     */
    function showMessage(message, type = 'info', container = null, duration = null) {
        let containerEl;
        
        if (typeof container === 'string') {
            containerEl = document.querySelector(container);
        } else if (container instanceof HTMLElement) {
            containerEl = container;
        } else {
            // Try common container IDs
            containerEl = document.getElementById('statusMessage') || 
                         document.getElementById('transferStatus') ||
                         document.getElementById('quantStatus') ||
                         document.getElementById('errorMessage');
        }

        if (!containerEl) {
            console.warn('No message container found');
            return;
        }

        const config = MESSAGE_TYPES[type] || MESSAGE_TYPES.info;
        const displayDuration = duration || config.duration;

        // Set message content and styling
        containerEl.innerHTML = message;
        containerEl.style.display = 'block';
        containerEl.style.background = config.background;
        containerEl.style.color = config.color;
        containerEl.style.padding = '15px';
        containerEl.style.borderRadius = '10px';
        containerEl.style.margin = '20px 0';
        containerEl.style.textAlign = 'center';
        containerEl.style.fontWeight = 'bold';
        containerEl.style.transition = 'all 0.3s ease';

        // Auto-hide after duration
        if (displayDuration > 0) {
            setTimeout(() => {
                containerEl.style.opacity = '0';
                setTimeout(() => {
                    containerEl.style.display = 'none';
                    containerEl.style.opacity = '1';
                }, 300);
            }, displayDuration);
        }
    }

    /**
     * Make an API request with consistent error handling
     * @param {string} url - The API endpoint URL
     * @param {object} options - Fetch options
     * @returns {Promise} The fetch promise
     */
    async function apiRequest(url, options = {}) {
        const defaultOptions = {
            ...API_CONFIG,
            ...options,
            headers: {
                ...API_CONFIG.headers,
                ...(options.headers || {})
            }
        };

        try {
            const response = await fetch(url, defaultOptions);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || data.message || `HTTP ${response.status}`);
            }

            // Handle redirects (e.g., quant independence, insider trading)
            if (data.redirect) {
                window.location.href = data.redirect;
                return null;
            }

            return data;
        } catch (error) {
            // Network or parsing error
            if (error instanceof TypeError) {
                throw new Error('Network error - please check your connection');
            }
            throw error;
        }
    }

    /**
     * Format a number with locale-specific formatting
     * @param {number} value - The number to format
     * @param {string} suffix - Optional suffix (e.g., 'STRAW', 'coins')
     * @returns {string} Formatted number string
     */
    function formatNumber(value, suffix = '') {
        if (value === null || value === undefined || isNaN(value)) {
            return 'N/A';
        }
        const formatted = value.toLocaleString();
        return suffix ? `${formatted} ${suffix}` : formatted;
    }

    /**
     * Format a number as currency with sign
     * @param {number} value - The number to format
     * @param {boolean} showPositive - Whether to show + for positive numbers
     * @returns {string} Formatted number string
     */
    function formatChange(value, showPositive = true) {
        if (value === null || value === undefined || isNaN(value)) {
            return 'N/A';
        }
        const formatted = Math.abs(value).toLocaleString();
        if (value > 0 && showPositive) {
            return `+${formatted}`;
        } else if (value < 0) {
            return `-${formatted}`;
        }
        return formatted;
    }

    /**
     * Update market statistics in the UI
     * @param {object} stats - Market statistics object
     */
    function updateMarketStats(stats) {
        // Update market cap
        const marketCapElements = document.querySelectorAll('[data-stat="market-cap"]');
        marketCapElements.forEach(el => {
            if (stats.market_cap !== undefined) {
                el.textContent = formatNumber(stats.market_cap);
            }
        });

        // Update user count
        const userCountElements = document.querySelectorAll('[data-stat="user-count"]');
        userCountElements.forEach(el => {
            if (stats.total_users !== undefined || stats.user_count !== undefined) {
                el.textContent = stats.total_users || stats.user_count;
            }
        });

        // Update volume
        const volumeElements = document.querySelectorAll('[data-stat="volume"]');
        volumeElements.forEach(el => {
            if (stats.total_volume !== undefined || stats.volume !== undefined) {
                el.textContent = formatNumber(stats.total_volume || stats.volume);
            }
        });

        // Update total coins (for quant terminal)
        const totalCoinsEl = document.getElementById('totalCoins');
        if (totalCoinsEl && stats.market_cap !== undefined) {
            totalCoinsEl.textContent = formatNumber(stats.market_cap);
        }

        // Update total users (for quant terminal)
        const totalUsersEl = document.getElementById('totalUsers');
        if (totalUsersEl && (stats.user_count !== undefined || stats.total_users !== undefined)) {
            totalUsersEl.textContent = stats.user_count || stats.total_users;
        }
    }

    /**
     * Check session status and redirect if expired
     * @param {string} redirectUrl - URL to redirect to if session expired
     */
    async function checkSession(redirectUrl = '/register') {
        try {
            const response = await fetch('/auth/session-status');
            const data = await response.json();
            
            if (!data.authenticated) {
                window.location.href = redirectUrl;
                return false;
            }
            return true;
        } catch (error) {
            console.error('Session check failed:', error);
            return false;
        }
    }

    /**
     * Clear all session data
     */
    function clearSession() {
        if (typeof Storage !== 'undefined') {
            localStorage.clear();
            sessionStorage.clear();
        }
    }

    /**
     * Add mobile touch optimizations to an element
     * @param {HTMLElement} element - The element to optimize
     * @param {object} options - Touch optimization options
     */
    function addTouchOptimization(element, options = {}) {
        const defaults = {
            scaleOnTouch: true,
            scaleFactor: 0.98,
            preventDefaultTouch: false
        };
        
        const settings = { ...defaults, ...options };

        if (settings.scaleOnTouch) {
            element.addEventListener('touchstart', function() {
                this.style.transform = `scale(${settings.scaleFactor})`;
            }, { passive: true });

            element.addEventListener('touchend', function() {
                this.style.transform = 'scale(1)';
            }, { passive: true });
        }

        if (settings.preventDefaultTouch) {
            element.addEventListener('touchstart', function(e) {
                e.preventDefault();
            });
        }
    }

    /**
     * Create and manage auto-refresh intervals
     * @param {function} callback - Function to call on each interval
     * @param {number} interval - Interval in milliseconds
     * @returns {object} Interval controller with start/stop methods
     */
    function createAutoRefresh(callback, interval) {
        let intervalId = null;

        return {
            start() {
                if (!intervalId) {
                    callback(); // Initial call
                    intervalId = setInterval(callback, interval);
                }
            },
            stop() {
                if (intervalId) {
                    clearInterval(intervalId);
                    intervalId = null;
                }
            },
            restart() {
                this.stop();
                this.start();
            },
            isRunning() {
                return intervalId !== null;
            }
        };
    }

    /**
     * Debounce a function
     * @param {function} func - Function to debounce
     * @param {number} wait - Wait time in milliseconds
     * @returns {function} Debounced function
     */
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    /**
     * Throttle a function
     * @param {function} func - Function to throttle
     * @param {number} limit - Time limit in milliseconds
     * @returns {function} Throttled function
     */
    function throttle(func, limit) {
        let inThrottle;
        return function(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }

    /**
     * Get current username from the page
     * @returns {string|null} Username or null if not found
     */
    function getCurrentUsername() {
        const usernameElement = document.querySelector('[data-username]');
        if (usernameElement) {
            return usernameElement.getAttribute('data-username');
        }
        // Fallback to window object
        return window.currentUsername || null;
    }

    /**
     * Validate username format
     * @param {string} username - Username to validate
     * @returns {object} Validation result with isValid and message
     */
    function validateUsername(username) {
        if (!username || username.trim().length === 0) {
            return { isValid: false, message: 'Username is required' };
        }
        
        const trimmed = username.trim();
        
        if (trimmed.length < 3) {
            return { isValid: false, message: 'Username must be at least 3 characters' };
        }
        
        if (!/^[a-zA-Z0-9_-]+$/.test(trimmed)) {
            return { isValid: false, message: 'Username can only contain letters, numbers, underscore, and hyphen' };
        }
        
        return { isValid: true, message: 'Valid username' };
    }

    /**
     * Create a modal dialog
     * @param {string} content - HTML content for the modal
     * @param {object} options - Modal options
     * @returns {HTMLElement} The modal element
     */
    function createModal(content, options = {}) {
        const defaults = {
            closeOnClick: true,
            showCloseButton: true,
            className: 'straw-modal'
        };
        
        const settings = { ...defaults, ...options };
        
        const modal = document.createElement('div');
        modal.className = settings.className;
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.9);
            z-index: 1000;
            display: flex;
            align-items: center;
            justify-content: center;
        `;
        
        const modalContent = document.createElement('div');
        modalContent.style.cssText = `
            background: #2c3e50;
            padding: 30px;
            border-radius: 15px;
            max-width: 600px;
            max-height: 80%;
            overflow-y: auto;
            position: relative;
        `;
        
        modalContent.innerHTML = content;
        
        if (settings.showCloseButton) {
            const closeBtn = document.createElement('button');
            closeBtn.innerHTML = '×';
            closeBtn.style.cssText = `
                position: absolute;
                top: 10px;
                right: 10px;
                background: none;
                border: none;
                color: white;
                font-size: 30px;
                cursor: pointer;
                padding: 0;
                width: 30px;
                height: 30px;
                line-height: 30px;
            `;
            closeBtn.onclick = () => modal.remove();
            modalContent.appendChild(closeBtn);
        }
        
        if (settings.closeOnClick) {
            modal.onclick = () => modal.remove();
            modalContent.onclick = (e) => e.stopPropagation();
        }
        
        modal.appendChild(modalContent);
        document.body.appendChild(modal);
        
        return modal;
    }

    // Public API
    return {
        // Message display
        showMessage,
        showSuccess: (msg, container, duration) => showMessage(msg, 'success', container, duration),
        showError: (msg, container, duration) => showMessage(msg, 'error', container, duration),
        showInfo: (msg, container, duration) => showMessage(msg, 'info', container, duration),
        showWarning: (msg, container, duration) => showMessage(msg, 'warning', container, duration),
        
        // API utilities
        apiRequest,
        
        // Formatting
        formatNumber,
        formatChange,
        
        // Market data
        updateMarketStats,
        
        // Session management
        checkSession,
        clearSession,
        
        // UI utilities
        addTouchOptimization,
        createAutoRefresh,
        createModal,
        
        // Function utilities
        debounce,
        throttle,
        
        // User utilities
        getCurrentUsername,
        validateUsername,
        
        // Constants
        REFRESH_INTERVALS,
        MESSAGE_TYPES
    };
})();

// Make available globally
window.StrawCoinUtils = StrawCoinUtils;