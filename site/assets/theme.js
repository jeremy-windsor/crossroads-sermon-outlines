(() => {
  const root = document.documentElement;
  const selector = document.querySelector('.theme-selector');
  const controls = Array.from(selector.querySelectorAll('[data-theme-choice]'));
  const system = window.matchMedia('(prefers-color-scheme: dark)');
  const selected = () => root.dataset.theme || 'system';
  const sync = () => {
    const choice = selected();
    for (const control of controls) {
      control.setAttribute('aria-pressed', String(control.dataset.themeChoice === choice));
    }
  };
  const apply = choice => {
    if (choice === 'system') {
      delete root.dataset.theme;
      try { localStorage.removeItem('crossroads-theme'); } catch (_) {}
    } else {
      root.dataset.theme = choice;
      try { localStorage.setItem('crossroads-theme', choice); } catch (_) {}
    }
    sync();
  };
  selector.hidden = false;
  for (const control of controls) {
    control.addEventListener('click', () => apply(control.dataset.themeChoice));
    control.addEventListener('keydown', event => {
      const keys = ['ArrowLeft', 'ArrowRight', 'Home', 'End'];
      if (!keys.includes(event.key)) return;
      event.preventDefault();
      const current = controls.indexOf(control);
      const next = event.key === 'Home' ? 0 : event.key === 'End' ? controls.length - 1
        : (current + (event.key === 'ArrowRight' ? 1 : -1) + controls.length) % controls.length;
      controls[next].focus();
      apply(controls[next].dataset.themeChoice);
    });
  }
  system.addEventListener('change', sync);
  sync();
})();
