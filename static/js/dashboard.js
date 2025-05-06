// Dashboard-specific JavaScript functionality

document.addEventListener('DOMContentLoaded', function() {
    // Initialize any dashboard-specific components
    initializeFilters();
    initializeCardInteractions();
    
    // Update dynamic elements
    updateTimestamps();
    
    // Initialize stats if present
    const statsContainer = document.getElementById('stats-container');
    if (statsContainer) {
        initializeStats();
    }
});

/**
 * Initialize filtering functionality for placements
 */
function initializeFilters() {
    const filterForm = document.getElementById('filter-form');
    if (!filterForm) return;
    
    // Handle filter form submission
    filterForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const filterType = document.getElementById('filter-type').value;
        const filterSource = document.getElementById('filter-source').value;
        const filterDate = document.getElementById('filter-date').value;
        
        // Apply filters to the placement cards
        const placementCards = document.querySelectorAll('.placement-card');
        placementCards.forEach(function(card) {
            let showCard = true;
            
            // Filter by media type
            if (filterType && filterType !== 'all') {
                const cardType = card.getAttribute('data-type');
                if (cardType !== filterType) {
                    showCard = false;
                }
            }
            
            // Filter by source
            if (filterSource && filterSource !== 'all') {
                const cardSource = card.getAttribute('data-source');
                if (cardSource !== filterSource) {
                    showCard = false;
                }
            }
            
            // Filter by date range
            if (filterDate && filterDate !== 'all') {
                const cardDate = new Date(card.getAttribute('data-date'));
                const now = new Date();
                
                if (filterDate === 'today') {
                    const today = new Date();
                    today.setHours(0, 0, 0, 0);
                    if (cardDate < today) {
                        showCard = false;
                    }
                } else if (filterDate === 'week') {
                    const weekAgo = new Date();
                    weekAgo.setDate(weekAgo.getDate() - 7);
                    if (cardDate < weekAgo) {
                        showCard = false;
                    }
                } else if (filterDate === 'month') {
                    const monthAgo = new Date();
                    monthAgo.setMonth(monthAgo.getMonth() - 1);
                    if (cardDate < monthAgo) {
                        showCard = false;
                    }
                }
            }
            
            // Show or hide card based on filter results
            card.style.display = showCard ? 'block' : 'none';
        });
        
        // Update filtered count
        updateFilteredCount();
    });
    
    // Handle filter reset
    const resetFilterBtn = document.getElementById('reset-filter');
    if (resetFilterBtn) {
        resetFilterBtn.addEventListener('click', function() {
            filterForm.reset();
            
            // Show all placement cards
            const placementCards = document.querySelectorAll('.placement-card');
            placementCards.forEach(function(card) {
                card.style.display = 'block';
            });
            
            // Update filtered count
            updateFilteredCount();
        });
    }
    
    // Populate unique sources for filter dropdown
    populateSourcesDropdown();
}

/**
 * Populate the sources dropdown with unique values from the placement cards
 */
function populateSourcesDropdown() {
    const sourceSelect = document.getElementById('filter-source');
    if (!sourceSelect) return;
    
    const sources = new Set();
    
    // Collect all unique sources from placement cards
    document.querySelectorAll('.placement-card').forEach(function(card) {
        const source = card.getAttribute('data-source');
        if (source) {
            sources.add(source);
        }
    });
    
    // Add options to the dropdown
    sources.forEach(function(source) {
        const option = document.createElement('option');
        option.value = source;
        option.textContent = source;
        sourceSelect.appendChild(option);
    });
}

/**
 * Update the filtered count display
 */
function updateFilteredCount() {
    const countElement = document.getElementById('filtered-count');
    if (!countElement) return;
    
    const visibleCards = document.querySelectorAll('.placement-card[style="display: block;"], .placement-card:not([style*="display"])').length;
    const totalCards = document.querySelectorAll('.placement-card').length;
    
    countElement.textContent = `Showing ${visibleCards} of ${totalCards} placements`;
}

/**
 * Initialize card interactions (hover effects, click actions)
 */
function initializeCardInteractions() {
    const placementCards = document.querySelectorAll('.card-hover');
    
    placementCards.forEach(function(card) {
        // Add click event for the whole card to navigate to detail view
        // but not if clicking on buttons or links within the card
        card.addEventListener('click', function(e) {
            if (!e.target.closest('a, button, .dropdown-menu')) {
                const detailUrl = this.getAttribute('data-detail-url');
                if (detailUrl) {
                    window.location.href = detailUrl;
                }
            }
        });
    });
    
    // Initialize any dropdowns or interactive elements within cards
    const copyLinkBtns = document.querySelectorAll('.copy-link-btn');
    copyLinkBtns.forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            const url = this.getAttribute('data-url');
            copyToClipboard(url)
                .then(() => {
                    // Show success feedback
                    const originalText = this.innerHTML;
                    this.innerHTML = '<i data-feather="check"></i> Copied!';
                    feather.replace();
                    
                    // Reset button text after 2 seconds
                    setTimeout(() => {
                        this.innerHTML = originalText;
                        feather.replace();
                    }, 2000);
                })
                .catch(err => {
                    console.error('Failed to copy: ', err);
                    alert('Failed to copy link to clipboard');
                });
        });
    });
}

/**
 * Update relative timestamps on the page
 */
function updateTimestamps() {
    const timestamps = document.querySelectorAll('.relative-time');
    
    timestamps.forEach(function(element) {
        const dateString = element.getAttribute('data-date');
        if (dateString) {
            element.textContent = formatDate(dateString, 'relative');
        }
    });
}

/**
 * Initialize statistics charts if they exist
 */
function initializeStats() {
    // Check if Chart.js is available
    if (typeof Chart === 'undefined') {
        console.warn('Chart.js is not loaded. Stats visualization is disabled.');
        return;
    }
    
    // Initialize media type distribution chart
    const typeChartCanvas = document.getElementById('media-type-chart');
    if (typeChartCanvas) {
        // Collect data from the page
        const typeData = {};
        document.querySelectorAll('.placement-card').forEach(function(card) {
            const type = card.getAttribute('data-type');
            if (type) {
                typeData[type] = (typeData[type] || 0) + 1;
            }
        });
        
        // Create chart
        new Chart(typeChartCanvas, {
            type: 'doughnut',
            data: {
                labels: Object.keys(typeData).map(key => key.charAt(0).toUpperCase() + key.slice(1)),
                datasets: [{
                    data: Object.values(typeData),
                    backgroundColor: [
                        '#007bff', '#28a745', '#ffc107', '#dc3545', '#6610f2', '#fd7e14', '#20c997'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right'
                    }
                }
            }
        });
    }
    
    // Initialize placement timeline chart
    const timelineChartCanvas = document.getElementById('timeline-chart');
    if (timelineChartCanvas) {
        // Collect data by month from the page
        const months = {};
        const now = new Date();
        
        // Initialize last 6 months
        for (let i = 5; i >= 0; i--) {
            const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
            const monthKey = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
            const monthLabel = d.toLocaleDateString(undefined, { month: 'short', year: 'numeric' });
            months[monthKey] = { count: 0, label: monthLabel };
        }
        
        // Count placements by month
        document.querySelectorAll('.placement-card').forEach(function(card) {
            const dateStr = card.getAttribute('data-date');
            if (dateStr) {
                const date = new Date(dateStr);
                const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
                
                if (months[monthKey]) {
                    months[monthKey].count++;
                }
            }
        });
        
        // Create chart
        new Chart(timelineChartCanvas, {
            type: 'line',
            data: {
                labels: Object.values(months).map(m => m.label),
                datasets: [{
                    label: 'Media Placements',
                    data: Object.values(months).map(m => m.count),
                    borderColor: '#007bff',
                    backgroundColor: 'rgba(0, 123, 255, 0.1)',
                    fill: true,
                    tension: 0.3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0
                        }
                    }
                }
            }
        });
    }
}
