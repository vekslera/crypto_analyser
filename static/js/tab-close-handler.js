/**
 * Tab Close Handler
 * Detects browser tab closing and sends shutdown request to server
 */

(function() {
    'use strict';
    
    // Configuration
    const CONFIG = {
        shutdownUrl: 'http://localhost:8000/system/shutdown',
        hiddenTabTimeout: 10000 // 10 seconds
    };
    
    /**
     * Send shutdown request to server
     */
    function sendShutdownRequest() {
        if (navigator.sendBeacon) {
            // Modern browsers - reliable method for page unload
            navigator.sendBeacon(CONFIG.shutdownUrl, '');
        } else {
            // Fallback for older browsers
            try {
                const xhr = new XMLHttpRequest();
                xhr.open('POST', CONFIG.shutdownUrl, false); // Synchronous request
                xhr.send();
            } catch (error) {
                console.warn('Failed to send shutdown request:', error);
            }
        }
    }
    
    /**
     * Handle browser tab/window closing
     */
    function handleBeforeUnload(event) {
        sendShutdownRequest();
        // Note: Don't prevent default or show confirmation dialog
        // as it would interfere with the user experience
    }
    
    /**
     * Handle tab visibility changes (user switches tabs)
     */
    function handleVisibilityChange() {
        if (document.hidden) {
            // Tab is now hidden - user might be closing
            localStorage.setItem('tabHidden', Date.now().toString());
        } else {
            // Tab is visible again - remove the hidden timestamp
            localStorage.removeItem('tabHidden');
        }
    }
    
    /**
     * Handle window focus (tab becomes active again)
     */
    function handleWindowFocus() {
        const hiddenTime = localStorage.getItem('tabHidden');
        if (hiddenTime && (Date.now() - parseInt(hiddenTime)) > CONFIG.hiddenTabTimeout) {
            // Tab was hidden for more than timeout period, likely closed and reopened
            localStorage.removeItem('tabHidden');
        }
    }
    
    /**
     * Initialize event listeners
     */
    function initialize() {
        // Primary tab close detection
        window.addEventListener('beforeunload', handleBeforeUnload);
        
        // Tab visibility tracking (helps with detection accuracy)
        document.addEventListener('visibilitychange', handleVisibilityChange);
        
        // Window focus tracking
        window.addEventListener('focus', handleWindowFocus);
        
        console.log('Tab close handler initialized');
    }
    
    /**
     * Cleanup function (if needed)
     */
    function cleanup() {
        window.removeEventListener('beforeunload', handleBeforeUnload);
        document.removeEventListener('visibilitychange', handleVisibilityChange);
        window.removeEventListener('focus', handleWindowFocus);
        localStorage.removeItem('tabHidden');
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initialize);
    } else {
        initialize();
    }
    
    // Expose cleanup function globally if needed
    window.tabCloseHandler = {
        cleanup: cleanup
    };
    
})();