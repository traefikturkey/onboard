(() => {
  document.querySelectorAll('[data-utility-menu]').forEach(menu => {
    const toggle = menu.querySelector('.utility-menu-toggle');
    const links = menu.querySelector('.utility-menu-links');
    let hoverTimer;

    function cancelHover() {
      clearTimeout(hoverTimer);
      hoverTimer = undefined;
    }

    function setOpen(open) {
      cancelHover();
      links.hidden = !open;
      toggle.setAttribute('aria-expanded', String(open));
    }

    menu.addEventListener('mouseenter', () => {
      cancelHover();
      if (links.hidden && window.matchMedia('(hover: hover)').matches) {
        hoverTimer = setTimeout(() => setOpen(true), 2000);
      }
    });
    menu.addEventListener('mouseleave', () => setOpen(false));
    menu.addEventListener('focusout', event => {
      if (!menu.contains(event.relatedTarget)) setOpen(false);
    });
    toggle.addEventListener('click', () => setOpen(links.hidden));
    menu.addEventListener('keydown', event => {
      if (event.key === 'Escape' && !links.hidden) {
        setOpen(false);
        toggle.focus();
        event.preventDefault();
      } else if (event.key === 'ArrowDown' && !links.contains(event.target)) {
        setOpen(true);
        links.querySelector('a')?.focus();
        event.preventDefault();
      }
    });
    document.addEventListener('click', event => {
      if (!menu.contains(event.target)) setOpen(false);
    });
  });
})();
