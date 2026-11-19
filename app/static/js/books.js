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
})();
