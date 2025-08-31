// GitLab MR Manager JavaScript

// Make mobile menu functions available immediately
window.openMobileMenu = function() {
    const sidebar = document.querySelector('.sidebar');
    const backdrop = document.querySelector('.mobile-backdrop');
    
    if (!sidebar || !backdrop) {
        console.error('Sidebar or backdrop not found');
        return;
    }
    
    sidebar.classList.add('open');
    backdrop.classList.add('show');
};

window.closeMobileMenu = function() {
    const sidebar = document.querySelector('.sidebar');
    const backdrop = document.querySelector('.mobile-backdrop');
    
    if (!sidebar || !backdrop) {
        console.error('Sidebar or backdrop not found');
        return;
    }
    
    sidebar.classList.remove('open');
    backdrop.classList.remove('show');
};

document.addEventListener('DOMContentLoaded', function() {
    // Initialize the application
    initApp();
});

function initApp() {
    // Add event listeners
    setupEventListeners();
    
    // Initialize tooltips and other UI elements
    setupUI();
    
    // Load initial data if needed
    loadInitialData();
    
    // Setup mobile menu functionality
    setupMobileMenu();
}

function setupEventListeners() {
    // MR item click handlers
    document.querySelectorAll('.mr-item').forEach(item => {
        item.addEventListener('click', function() {
            const mrId = this.dataset.mrId;
            if (mrId) {
                openMRDetails(mrId);
            }
        });
    });

    // Filter handlers
    const filterSelects = document.querySelectorAll('.filter-select');
    filterSelects.forEach(select => {
        select.addEventListener('change', function() {
            applyFilters();
        });
    });

    // Search functionality
    const searchInput = document.querySelector('.search-input');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(function() {
            performSearch(this.value);
        }, 300));
    }

    // Button handlers
    document.querySelectorAll('.btn-approve').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.stopPropagation();
            const mrId = this.dataset.mrId;
            approveMR(mrId);
        });
    });

    document.querySelectorAll('.btn-merge').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.stopPropagation();
            const mrId = this.dataset.mrId;
            mergeMR(mrId);
        });
    });

    document.querySelectorAll('.btn-close').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.stopPropagation();
            const mrId = this.dataset.mrId;
            closeMR(mrId);
        });
    });

    // Label click handlers for filtering
    document.querySelectorAll('.label').forEach(label => {
        label.addEventListener('click', function(e) {
            e.stopPropagation();
            const labelText = this.textContent;
            filterByLabel(labelText);
        });
    });
}

function setupUI() {
    // Add loading states
    addLoadingStates();
    
    // Initialize tooltips
    initTooltips();
    
    // Add smooth scrolling
    addSmoothScrolling();
}

function addLoadingStates() {
    // Add loading spinner to buttons when clicked
    document.querySelectorAll('.btn').forEach(btn => {
        btn.addEventListener('click', function() {
            if (!this.classList.contains('btn-disabled')) {
                this.classList.add('loading');
                const originalText = this.innerHTML;
                this.innerHTML = '<div class="spinner"></div> Loading...';
                
                // Reset after a delay (in real app, this would be after API call)
                setTimeout(() => {
                    this.classList.remove('loading');
                    this.innerHTML = originalText;
                }, 2000);
            }
        });
    });
}

function initTooltips() {
    // Simple tooltip implementation
    document.querySelectorAll('[data-tooltip]').forEach(element => {
        element.addEventListener('mouseenter', function() {
            const tooltip = document.createElement('div');
            tooltip.className = 'tooltip';
            tooltip.textContent = this.dataset.tooltip;
            tooltip.style.cssText = `
                position: absolute;
                background: #1e293b;
                color: white;
                padding: 0.5rem;
                border-radius: 4px;
                font-size: 0.75rem;
                z-index: 1000;
                pointer-events: none;
            `;
            
            document.body.appendChild(tooltip);
            
            const rect = this.getBoundingClientRect();
            tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
            tooltip.style.top = rect.top - tooltip.offsetHeight - 5 + 'px';
        });
        
        element.addEventListener('mouseleave', function() {
            const tooltip = document.querySelector('.tooltip');
            if (tooltip) {
                tooltip.remove();
            }
        });
    });
}

function addSmoothScrolling() {
    // Smooth scroll to top when clicking on navigation
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

function loadInitialData() {
    // Badge counts are now handled by the /api/stats endpoint in base.html
    
    // Load any cached filters
    loadCachedFilters();
}

function updateMRCounts() {
    // This function is deprecated - badge counts are now handled by the /api/stats endpoint
    // and updated in base.html via JavaScript
    console.log('updateMRCounts() is deprecated - using /api/stats instead');
}

function applyFilters() {
    const filters = getActiveFilters();
    const mrItems = document.querySelectorAll('.mr-item');
    
    mrItems.forEach(item => {
        let shouldShow = true;
        
        // Apply label filter
        if (filters.label && filters.label !== 'all') {
            const labels = Array.from(item.querySelectorAll('.label')).map(l => l.textContent);
            if (!labels.includes(filters.label)) {
                shouldShow = false;
            }
        }
        
        // Apply status filter
        if (filters.status && filters.status !== 'all') {
            if (item.dataset.status !== filters.status) {
                shouldShow = false;
            }
        }
        
        // Apply author filter
        if (filters.author && filters.author !== 'all') {
            const author = item.querySelector('.mr-author').textContent;
            if (author !== filters.author) {
                shouldShow = false;
            }
        }
        
        // Show/hide item
        item.style.display = shouldShow ? 'block' : 'none';
    });
    
    // Update empty state
    updateEmptyState();
    
    // Cache filters
    cacheFilters(filters);
}

function getActiveFilters() {
    const filters = {};
    
    document.querySelectorAll('.filter-select').forEach(select => {
        if (select.value && select.value !== 'all') {
            filters[select.name] = select.value;
        }
    });
    
    return filters;
}

function filterByLabel(labelText) {
    // Set the label filter and apply
    const labelFilter = document.querySelector('select[name="label"]');
    if (labelFilter) {
        labelFilter.value = labelText;
        applyFilters();
    }
}

function performSearch(query) {
    const mrItems = document.querySelectorAll('.mr-item');
    
    mrItems.forEach(item => {
        const title = item.querySelector('.mr-title').textContent.toLowerCase();
        const author = item.querySelector('.mr-author').textContent.toLowerCase();
        const labels = Array.from(item.querySelectorAll('.label')).map(l => l.textContent.toLowerCase());
        
        const matches = title.includes(query.toLowerCase()) ||
                       author.includes(query.toLowerCase()) ||
                       labels.some(label => label.includes(query.toLowerCase()));
        
        item.style.display = matches ? 'block' : 'none';
    });
    
    updateEmptyState();
}

function updateEmptyState() {
    const visibleItems = document.querySelectorAll('.mr-item[style*="block"], .mr-item:not([style*="none"])');
    const emptyState = document.querySelector('.empty-state');
    
    if (visibleItems.length === 0 && emptyState) {
        emptyState.style.display = 'block';
    } else if (emptyState) {
        emptyState.style.display = 'none';
    }
}

function openMRDetails(mrId) {
    // Debug breakpoint - this will pause execution in browser dev tools
    //debugger;
    
    // In a real application, this would open a modal or navigate to MR details
    console.log(`Opening MR details for ID: ${mrId}`);
    console.log('Dummy ErrorFunction called from:', new Error().stack);
    
    // Log additional context
    const mrElement = document.querySelector(`[data-mr-id="${mrId}"]`);
    if (mrElement) {
        console.log('MR Element found:', mrElement);
        console.log('MR Title:', mrElement.querySelector('.mr-title')?.textContent);
    }
    
    // Get the GitLab MR URL from the element's data attribute or construct it
    let gitlabUrl = mrElement?.dataset?.webUrl;
    
    if (!gitlabUrl) {
        // Fallback: construct the URL using the GitLab instance and project
        const gitlabBaseUrl = 'https://git.csez.zohocorpin.com';
        const projectId = '16895';
        gitlabUrl = `${gitlabBaseUrl}/zohofinance/zohopages/page-builder/-/merge_requests/${mrId}`;
    }
    
    console.log('Opening GitLab MR URL:', gitlabUrl);
    
    // Open the GitLab MR page in a new tab
    window.open(gitlabUrl, '_blank');
}

function approveMR(mrId) {
    if (confirm(`Are you sure you want to approve MR #${mrId}?`)) {
        showNotification(`Approving MR #${mrId}...`, 'info');
        
        fetch(`/api/mrs/${mrId}/approve`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification(`MR #${mrId} approved successfully!`, 'success');
                // Reload the page to get updated data
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            } else {
                showNotification(`Error: ${data.message}`, 'error');
            }
        })
        .catch(error => {
            showNotification(`Error approving MR: ${error.message}`, 'error');
        });
    }
}

function mergeMR(mrId) {
    if (confirm(`Are you sure you want to merge MR #${mrId}?`)) {
        showNotification(`Merging MR #${mrId}...`, 'info');
        
        fetch(`/api/mrs/${mrId}/merge`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification(`MR #${mrId} merged successfully!`, 'success');
                // Reload the page to get updated data
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            } else {
                showNotification(`Error: ${data.message}`, 'error');
            }
        })
        .catch(error => {
            showNotification(`Error merging MR: ${error.message}`, 'error');
        });
    }
}

function closeMR(mrId) {
    if (confirm(`Are you sure you want to close MR #${mrId}?`)) {
        showNotification(`Closing MR #${mrId}...`, 'info');
        
        fetch(`/api/mrs/${mrId}/close`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification(`MR #${mrId} closed successfully!`, 'success');
                // Reload the page to get updated data
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            } else {
                showNotification(`Error: ${data.message}`, 'error');
            }
        })
        .catch(error => {
            showNotification(`Error closing MR: ${error.message}`, 'error');
        });
    }
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas fa-${getNotificationIcon(type)}"></i>
            <span>${message}</span>
        </div>
        <button class="notification-close">&times;</button>
    `;
    
    // Add styles
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${getNotificationColor(type)};
        color: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        z-index: 1000;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        max-width: 400px;
        animation: slideIn 0.3s ease;
    `;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        notification.remove();
    }, 5000);
    
    // Close button handler
    notification.querySelector('.notification-close').addEventListener('click', () => {
        notification.remove();
    });
}

function getNotificationIcon(type) {
    const icons = {
        'success': 'check-circle',
        'error': 'exclamation-circle',
        'warning': 'exclamation-triangle',
        'info': 'info-circle'
    };
    return icons[type] || 'info-circle';
}

function getNotificationColor(type) {
    const colors = {
        'success': '#10b981',
        'error': '#ef4444',
        'warning': '#f59e0b',
        'info': '#3b82f6'
    };
    return colors[type] || '#3b82f6';
}

function cacheFilters(filters) {
    localStorage.setItem('mr-filters', JSON.stringify(filters));
}

function loadCachedFilters() {
    const cached = localStorage.getItem('mr-filters');
    if (cached) {
        const filters = JSON.parse(cached);
        Object.entries(filters).forEach(([name, value]) => {
            const select = document.querySelector(`select[name="${name}"]`);
            if (select) {
                select.value = value;
            }
        });
        applyFilters();
    }
}

// Utility function for debouncing
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

// Add CSS for notifications
const notificationStyles = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    .notification-content {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        flex: 1;
    }
    
    .notification-close {
        background: none;
        border: none;
        color: white;
        font-size: 1.25rem;
        cursor: pointer;
        padding: 0;
        width: 20px;
        height: 20px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    .notification-close:hover {
        opacity: 0.8;
    }
`;

// Inject notification styles
const styleSheet = document.createElement('style');
styleSheet.textContent = notificationStyles;
document.head.appendChild(styleSheet);

// Mobile menu functionality
function setupMobileMenu() {
    // Add event listener to the mobile toggle button as a fallback
    const mobileToggle = document.querySelector('.mobile-menu-toggle');
    if (mobileToggle) {
        mobileToggle.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            window.openMobileMenu();
        });
    }
    
    // Add event listener to the mobile close button as a fallback
    const mobileClose = document.querySelector('.mobile-menu-close');
    if (mobileClose) {
        mobileClose.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            window.closeMobileMenu();
        });
    }
}
