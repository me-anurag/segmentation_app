// Apply saved theme on load
document.addEventListener("DOMContentLoaded", () => {
    const themeToggle = document.getElementById('themeToggle');
  
    if (localStorage.getItem('theme') === 'dark') {
      document.body.classList.add('dark-mode');
      themeToggle.textContent = '☀️';
    }
  
    themeToggle.addEventListener('click', () => {
      document.body.classList.toggle('dark-mode');
      const isDark = document.body.classList.contains('dark-mode');
      themeToggle.textContent = isDark ? '☀️' : '🌙';
      localStorage.setItem('theme', isDark ? 'dark' : 'light');
    });
  
    // Manual dropdown toggle
    const manualToggle = document.getElementById('manualToggle');
    const manualDropdown = document.getElementById('manualDropdown');
  
    manualToggle.addEventListener('click', () => {
      manualDropdown.classList.toggle('manual-visible');
      manualDropdown.classList.toggle('manual-hidden');
    });
  });
  