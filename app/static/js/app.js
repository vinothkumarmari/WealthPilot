// MoneyManager Pro - Main JavaScript

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
