// Preview on hover or keyboard focus; use the Details button to pin it on touch.
(() => {
  const catalog = document.querySelector('.books-catalog');
  if (!catalog || !('showPopover' in HTMLElement.prototype)) return;

  let active = null;
  let closeTimer;

  function close() {
    clearTimeout(closeTimer);
    if (!active) return;
    active.panel.hidePopover();
    active.button.setAttribute('aria-expanded', 'false');
    active.pinned = false;
    active = null;
  }

  function position() {
    if (!active) return;
    const { link, panel, row } = active;
    const anchor = link.getBoundingClientRect();
    const gap = 8;
    if (anchor.bottom < 0 || anchor.top > window.innerHeight) {
      close();
      return;
    }
    const { width, height } = panel.getBoundingClientRect();
    const beside = row.getBoundingClientRect().right + gap;
    const right = document.documentElement.clientWidth - width - gap;
    const below = anchor.bottom + gap;
    const top = beside <= right ? anchor.top : (
      below + height <= window.innerHeight ? below : anchor.top - height - gap
    );
    panel.style.left = `${Math.max(gap, Math.min(beside <= right ? beside : anchor.left, right))}px`;
    panel.style.top = `${Math.max(gap, Math.min(top, window.innerHeight - height - gap))}px`;
  }

  function open(item) {
    clearTimeout(closeTimer);
    if (active === item || active?.pinned) return;
    close();
    active = item;
    item.panel.showPopover();
    item.button.setAttribute('aria-expanded', 'true');
    const image = item.panel.querySelector('img[data-cover]');
    if (image && !image.hasAttribute('src')) {
      image.addEventListener('error', () => image.remove(), { once: true });
      image.addEventListener('load', position, { once: true });
      image.src = image.dataset.cover;
    }
    position();
  }

  function leave(item) {
    clearTimeout(closeTimer);
    closeTimer = setTimeout(() => {
      if (active === item && !item.pinned &&
          !item.row.contains(document.activeElement) &&
          !item.panel.matches(':hover')) close();
    }, 180);
  }

  for (const button of catalog.querySelectorAll('.book-details-toggle')) {
    const row = button.closest('.book-row');
    const link = row.querySelector('a');
    const panel = document.getElementById(button.getAttribute('aria-controls'));
    const item = { row, link, button, panel, pinned: false };
    button.hidden = false;

    row.addEventListener('pointerenter', event => {
      if (event.pointerType === 'mouse') open(item);
    });
    row.addEventListener('pointerleave', () => leave(item));
    panel.addEventListener('pointerenter', () => clearTimeout(closeTimer));
    panel.addEventListener('pointerleave', () => leave(item));

    row.addEventListener('focusin', event => {
      if (event.target === link && link.matches(':focus-visible')) open(item);
    });
    row.addEventListener('focusout', event => {
      if (active === item && !row.contains(event.relatedTarget)) close();
    });

    button.addEventListener('click', () => {
      if (active === item && item.pinned) {
        close();
      } else {
        if (active && active !== item) close();
        open(item);
        if (active === item) item.pinned = true;
      }
    });
  }

  document.addEventListener('keydown', event => {
    if (event.key === 'Escape') close();
  });
  document.addEventListener('pointerdown', event => {
    if (active && !active.row.contains(event.target)) close();
  });
  window.addEventListener('resize', position);
  window.addEventListener('scroll', position);
})();
