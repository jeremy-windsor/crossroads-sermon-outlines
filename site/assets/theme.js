(() => {
  const root = document.documentElement;
  const toggle = document.querySelector('.theme-toggle');
  const reset = document.querySelector('.theme-reset');
  const system = window.matchMedia('(prefers-color-scheme: dark)');
  const isDark = () => root.dataset.theme ? root.dataset.theme === 'dark' : system.matches;
  const sync = () => {
    toggle.setAttribute('aria-pressed', String(isDark()));
    reset.hidden = !root.dataset.theme;
  };
  toggle.hidden = false;
  toggle.addEventListener('click', () => {
    root.dataset.theme = isDark() ? 'light' : 'dark';
    try { localStorage.setItem('crossroads-theme', root.dataset.theme); } catch (_) {}
    sync();
  });
  reset.addEventListener('click', () => {
    delete root.dataset.theme;
    try { localStorage.removeItem('crossroads-theme'); } catch (_) {}
    sync();
    toggle.focus();
  });
  system.addEventListener('change', sync);
  sync();
})();
