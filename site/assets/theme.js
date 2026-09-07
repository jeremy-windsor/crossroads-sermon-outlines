(() => {
  const root = document.documentElement;
  const toggle = document.querySelector('.theme-toggle');
  const icons = Array.from(toggle.querySelectorAll('[data-theme-icon]'));
  const system = window.matchMedia('(prefers-color-scheme: dark)');
  const current = () => root.dataset.theme || (system.matches ? 'dark' : 'light');
  const sync = () => {
    const target = current() === 'dark' ? 'light' : 'dark';
    const label = `Switch to ${target} theme`;
    toggle.setAttribute('aria-label', label);
    toggle.setAttribute('title', label);
    for (const icon of icons) {
      // SVG elements do not reflect the `hidden` IDL property, so set the attribute.
      icon.toggleAttribute('hidden', icon.dataset.themeIcon !== target);
    }
  };
  const apply = choice => {
    root.dataset.theme = choice;
    try { localStorage.setItem('crossroads-theme', choice); } catch (_) {}
    sync();
  };
  toggle.hidden = false;
  toggle.addEventListener('click', () => apply(current() === 'dark' ? 'light' : 'dark'));
  system.addEventListener('change', sync);
  sync();
})();
