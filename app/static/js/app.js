// MoneyManager Pro - Main JavaScript

// ============ CSRF TOKEN FOR AJAX ============
(function() {
    const csrfMeta = document.querySelector('meta[name="csrf-token"]');
    if (csrfMeta) {
        const csrfToken = csrfMeta.getAttribute('content');
        const origFetch = window.fetch;
        window.fetch = function(url, options) {
            options = options || {};
            if (options.method && ['POST', 'PUT', 'DELETE', 'PATCH'].includes(options.method.toUpperCase())) {
                options.headers = options.headers || {};
                // For FormData, set as header; for JSON, set as header
                if (options.body instanceof FormData) {
                    options.body.append('csrf_token', csrfToken);
                } else {
                    if (typeof options.headers === 'object' && !(options.headers instanceof Headers)) {
                        options.headers['X-CSRFToken'] = csrfToken;
                    }
                }
            }
            return origFetch.call(this, url, options);
        };
    }
})();

// Chart.js color palette
const chartColors = [
    '#6C5CE7', '#00CEC9', '#FD79A8', '#FDCB6E', '#E17055',
    '#0984E3', '#00B894', '#D63031', '#6C5CE7', '#A29BFE',
    '#55EFC4', '#81ECEC', '#74B9FF', '#DFE6E9', '#B2BEC3'
];

// Sidebar toggle for mobile
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.toggle('show');
}

// Sidebar expand/collapse for desktop (button click)
function toggleSidebarExpand() {
    const sidebar = document.getElementById('sidebar');
    const isExpanded = sidebar.classList.toggle('expanded');
    localStorage.setItem('sidebar_expanded', isExpanded ? '1' : '0');
    // Update main-content margin
    const main = document.querySelector('.main-content');
    if (main) {
        main.style.marginLeft = isExpanded ? 'var(--sidebar-width)' : 'var(--sidebar-collapsed-width)';
    }
    // Update icon
    const icon = document.getElementById('sidebarExpandIcon');
    if (icon) icon.textContent = isExpanded ? 'menu_open' : 'menu';
}

// Restore sidebar state from localStorage
(function() {
    const saved = localStorage.getItem('sidebar_expanded');
    if (saved === '1') {
        const sidebar = document.getElementById('sidebar');
        if (sidebar) sidebar.classList.add('expanded');
        const main = document.querySelector('.main-content');
        if (main) main.style.marginLeft = 'var(--sidebar-width)';
        const icon = document.getElementById('sidebarExpandIcon');
        if (icon) icon.textContent = 'menu_open';
    }
})();

// Close sidebar on outside click (mobile)
document.addEventListener('click', function(e) {
    const sidebar = document.getElementById('sidebar');
    const toggle = document.querySelector('.sidebar-toggle');
    if (sidebar && window.innerWidth < 992) {
        if (!sidebar.contains(e.target) && toggle && !toggle.contains(e.target)) {
            sidebar.classList.remove('show');
        }
    }
});

// Theme toggle (light/dark)
function toggleTheme() {
    const html = document.documentElement;
    const currentTheme = html.getAttribute('data-bs-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    html.setAttribute('data-bs-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    
    const icon = document.getElementById('themeIcon');
    if (icon) {
        icon.textContent = newTheme === 'dark' ? 'light_mode' : 'dark_mode';
    }
}

// Load saved theme
(function() {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        document.documentElement.setAttribute('data-bs-theme', savedTheme);
        const icon = document.getElementById('themeIcon');
        if (icon) {
            icon.textContent = savedTheme === 'dark' ? 'light_mode' : 'dark_mode';
        }
    }
})();

// Format Indian currency
function formatINR(amount) {
    return '₹' + Number(amount).toLocaleString('en-IN', { maximumFractionDigits: 0 });
}

// Auto-dismiss alerts after 5 seconds
document.querySelectorAll('.alert-dismissible').forEach(function(alert) {
    setTimeout(function() {
        const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
        bsAlert.close();
    }, 5000);
});

// ============ TABLE SEARCH & FILTER ============

// Full-text search across all visible columns
function filterTable(tableId, query) {
    const table = document.getElementById(tableId);
    if (!table) return;
    const rows = table.querySelectorAll('tbody tr');
    const q = query.toLowerCase().trim();
    rows.forEach(row => {
        if (row.cells.length <= 1) return; // skip "no records" rows
        const text = row.textContent.toLowerCase();
        row.style.display = q === '' || text.includes(q) ? '' : 'none';
    });
}

// Filter by specific column value (badge text or cell text)
function filterTableByCol(tableId, colIndex, value) {
    const table = document.getElementById(tableId);
    if (!table) return;
    const rows = table.querySelectorAll('tbody tr');
    rows.forEach(row => {
        if (row.cells.length <= 1) return;
        const cell = row.cells[colIndex];
        if (!cell) return;
        const cellText = cell.textContent.trim();
        row.style.display = value === '' || cellText === value ? '' : 'none';
    });
    // Also clear the text search when filter changes
    const searchInput = table.closest('.card').querySelector('input[type="text"]');
    if (searchInput) searchInput.value = '';
}
