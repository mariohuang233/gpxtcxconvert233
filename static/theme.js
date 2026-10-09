// Load before paint; preference storage may be unavailable in private browsing.
try {
  const theme = localStorage.getItem('theme');
  document.documentElement.dataset.theme = theme === 'light' ? 'light' : 'dark';
} catch { /* system preference remains active */ }
