/**
 * Main JavaScript file for the AI-Powered Freshdesk Ticket Assistant
 */

// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Refresh tickets button animation
    const refreshBtn = document.getElementById('refreshTicketsBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            const icon = this.querySelector('.fa-sync-alt');
            if (icon) {
                icon.classList.add('spinning');
                
                // Remove the spinning class after the refresh is complete
                // This is handled in the AJAX success callback in dashboard.html
            }
        });
    }
    
    // Auto-hide alerts after 5 seconds
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert:not(.alert-danger)');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
});

/**
 * Format a date as a relative time string (e.g., "2 hours ago")
 * 
 * @param {Date|string} date - The date to format
 * @returns {string} - Formatted relative time string
 */
function timeAgo(date) {
    if (!date) return '';
    
    const now = new Date();
    const past = new Date(date);
    const seconds = Math.floor((now - past) / 1000);
    
    // Less than a minute
    if (seconds < 60) {
        return 'just now';
    }
    
    // Less than an hour
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) {
        return minutes === 1 ? '1 minute ago' : `${minutes} minutes ago`;
    }
    
    // Less than a day
    const hours = Math.floor(minutes / 60);
    if (hours < 24) {
        return hours === 1 ? '1 hour ago' : `${hours} hours ago`;
    }
    
    // Less than a week
    const days = Math.floor(hours / 24);
    if (days < 7) {
        return days === 1 ? '1 day ago' : `${days} days ago`;
    }
    
    // Less than a month
    const weeks = Math.floor(days / 7);
    if (weeks < 4) {
        return weeks === 1 ? '1 week ago' : `${weeks} weeks ago`;
    }
    
    // Format as date
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    return past.toLocaleDateString(undefined, options);
}

/**
 * Truncate text to a specified length and add ellipsis
 * 
 * @param {string} text - The text to truncate
 * @param {number} length - Maximum length before truncation
 * @returns {string} - Truncated text with ellipsis if needed
 */
function truncateText(text, length = 100) {
    if (!text) return '';
    if (text.length <= length) return text;
    
    return text.substring(0, length) + '...';
}

/**
 * Show a confirmation dialog
 * 
 * @param {string} message - The confirmation message
 * @param {Function} onConfirm - Callback function to execute if confirmed
 * @param {Function} onCancel - Callback function to execute if cancelled
 */
function confirmAction(message, onConfirm, onCancel = null) {
    if (confirm(message)) {
        if (typeof onConfirm === 'function') {
            onConfirm();
        }
    } else if (typeof onCancel === 'function') {
        onCancel();
    }
}
