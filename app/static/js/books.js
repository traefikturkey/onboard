(() => {
  const catalog = document.querySelector('.books-catalog');
  if (!catalog) return;

  catalog.addEventListener('error', event => {
    if (event.target.matches('.book-cover-image')) event.target.hidden = true;
  }, true);
  // Cached failures can finish before the listener is attached.
  for (const image of catalog.querySelectorAll('.book-cover-image')) {
    if (image.complete && !image.naturalWidth) image.hidden = true;
  }

  initHoverPreview(catalog);

  const filters = catalog.querySelector('.books-filters');
  if (!filters) return;

  const search = filters.querySelector('#books-search');
  const folder = filters.querySelector('#books-folder');
  const clear = filters.querySelector('#books-clear');
  const status = filters.querySelector('#books-result-count');
  const empty = filters.querySelector('#books-no-results');
  const selectedLabel = filters.querySelector('#books-topics-selected');
  const normalize = text => text.normalize('NFD').replace(/\p{M}/gu, '').toLowerCase();
  const entries = Array.from(catalog.querySelectorAll('.book-tile'), tile => {
    const topics = JSON.parse(tile.dataset.topics);
    return {
      tile,
      folder: tile.dataset.folder,
      search: normalize(tile.dataset.search),
      topics: new Set(topics.length ? topics : ['']),
      details: tile.querySelector('.book-details'),
    };
  });
  const chips = Array.from(filters.querySelectorAll('[data-topic]'));
  const selected = new Set();

  function update() {
    const terms = normalize(search.value).trim().split(/\s+/).filter(Boolean);
    const selectedTopics = [...selected];
    const counts = new Map();
    let total = 0;
    for (const entry of entries) {
      const matches = (!folder.value || entry.folder === folder.value) &&
        terms.every(term => entry.search.includes(term)) &&
        selectedTopics.every(topic => entry.topics.has(topic));
      const hide = !matches;
      if (entry.tile.hidden !== hide) {
        if (hide) entry.details.hidePopover?.();
        entry.tile.hidden = hide;
      }
      if (!matches) continue;
      total += 1;
      // Adding a chip keeps only the current matches that also have its topic.
      for (const topic of entry.topics) counts.set(topic, (counts.get(topic) || 0) + 1);
    }

    for (const chip of chips) {
      const topic = chip.dataset.topic;
      const count = counts.get(topic) || 0;
      const pressed = selected.has(topic);
      chip.setAttribute('aria-pressed', String(pressed));
      chip.disabled = !pressed && count === 0;
      chip.querySelector('.books-topic-count').textContent = count;
    }
    if (selectedLabel) {
      selectedLabel.textContent = selected.size ? ` (${selected.size} selected)` : '';
    }
    status.textContent = `${total} ${total === 1 ? 'book' : 'books'}`;
    empty.hidden = total !== 0;
    clear.disabled = !search.value && !folder.value && !selected.size;
  }

  search.addEventListener('input', update);
  folder.addEventListener('change', update);
  for (const chip of chips) {
    chip.addEventListener('click', () => {
      const topic = chip.dataset.topic;
      if (!selected.delete(topic)) selected.add(topic);
      update();
    });
  }
  clear.addEventListener('click', () => {
    search.value = '';
    folder.value = '';
    selected.clear();
    search.focus();
    update();
  });

  update();
  filters.hidden = false;

  function initHoverPreview(root) {
    const preview = root.querySelector('.book-hover-preview');
    if (!preview?.showPopover) return;
    const desktop = matchMedia('(hover: hover) and (pointer: fine)');
    const gap = 8;
    let openTimer;
    let closeTimer;
    let warmUntil = 0;
    let pointerPosition;
    let dismissedPosition;

    const positionOf = event => `${event.clientX},${event.clientY}`;
    root.addEventListener('pointermove', event => {
      pointerPosition = positionOf(event);
    });

    function dismiss() {
      clearTimeout(openTimer);
      clearTimeout(closeTimer);
      warmUntil = 0;
      // Hiding a card can cause a pointerenter on the tile underneath it.
      dismissedPosition = pointerPosition;
      preview.hidePopover();
    }

    function show(link) {
      if (!link.matches(':hover') || link.closest('[hidden]') ||
          root.querySelector('.book-details:popover-open')) return;

      const anchor = link.getBoundingClientRect();
      const viewport = document.documentElement;
      const width = Math.min(288, viewport.clientWidth - 2 * gap);
      const right = anchor.right + gap;
      const left = anchor.left - gap - width;
      const fitsRight = right + width + gap <= viewport.clientWidth;
      if (!fitsRight && left < gap) {
        dismiss();
        return;
      }

      const title = document.createElement('div');
      title.className = 'book-preview-title';
      title.textContent = link.querySelector('.book-title').textContent;
      const details = link.closest('.book-tile').querySelector('.book-details');
      const content = ['.book-subtitle', '.book-byline', '.book-publication', '.book-summary', '.book-topic-list']
        .map(selector => details.querySelector(selector))
        .filter(Boolean)
        .map(field => field.cloneNode(true));
      preview.replaceChildren(title, ...content);
      preview.style.setProperty('--book-preview-offset', fitsRight ? '-4px' : '4px');
      preview.style.left = `${fitsRight ? right : left}px`;
      preview.showPopover();
      const bottomLimit = viewport.clientHeight - preview.offsetHeight - gap;
      preview.style.top = `${Math.max(gap, Math.min(anchor.top, bottomLimit))}px`;
    }

    function leave() {
      clearTimeout(openTimer);
      if (!preview.matches(':popover-open')) return;
      warmUntil = performance.now() + 300;
      clearTimeout(closeTimer);
      closeTimer = setTimeout(() => preview.hidePopover(), 150);
    }

    for (const link of root.querySelectorAll('.book-link')) {
      link.addEventListener('pointerenter', event => {
        if (!desktop.matches || !['mouse', 'pen'].includes(event.pointerType) ||
            positionOf(event) === dismissedPosition) return;
        dismissedPosition = undefined;
        clearTimeout(openTimer);
        clearTimeout(closeTimer);
        openTimer = setTimeout(() => show(link), performance.now() < warmUntil ? 0 : 300);
      });
      link.addEventListener('pointerleave', leave);
    }
    preview.addEventListener('pointerenter', () => clearTimeout(closeTimer));
    preview.addEventListener('pointerleave', leave);
    root.addEventListener('pointerover', event => {
      if (event.target.closest('.book-details-toggle')) dismiss();
    });
    root.addEventListener('beforetoggle', event => {
      if (event.newState === 'open' && event.target.matches('.book-details')) dismiss();
    }, true);
    document.addEventListener('pointerdown', event => {
      if (!preview.contains(event.target)) dismiss();
    }, true);
    document.addEventListener('keydown', event => {
      if (event.key === 'Escape') dismiss();
    });
    document.addEventListener('visibilitychange', dismiss);
    window.addEventListener('scroll', dismiss, { capture: true, passive: true });
    window.addEventListener('resize', dismiss);
    window.addEventListener('blur', dismiss);
    desktop.addEventListener('change', dismiss);
  }
})();
