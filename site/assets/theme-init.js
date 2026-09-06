/* Runs before the stylesheet so a saved preference applies before first paint. */
try {
  const savedTheme = localStorage.getItem('crossroads-theme');
  if (savedTheme === 'light' || savedTheme === 'dark') {
    document.documentElement.dataset.theme = savedTheme;
  }
} catch (_) { /* Storage can be unavailable; the system palette remains readable. */ }
