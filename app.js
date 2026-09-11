const PAGE_SIZE = 96;
const state = { games: [], source: 'All', query: '', visibleLimit: PAGE_SIZE };

const grid = document.querySelector('#game-grid');
const count = document.querySelector('#game-count');
const empty = document.querySelector('#empty-state');
const filters = document.querySelector('#source-filters');
const search = document.querySelector('#search');
const template = document.querySelector('#card-template');
const dialog = document.querySelector('#player');
const frame = document.querySelector('#game-frame');
const showMore = document.querySelector('#show-more');

function initials(title) {
  return title.split(/\s+/).slice(0, 2).map(word => word[0] || '').join('').toUpperCase();
}

function gameURL(game) {
  const target = new URL(game.url, location.href);
  if (game.local && target.origin === location.origin) return target.href;
  if (!game.local && ['http:', 'https:'].includes(target.protocol)) return target.href;
  throw new Error(`Unsafe game URL for ${game.id}`);
}

function imageURL(value) {
  const target = new URL(value, location.href);
  if (target.origin === location.origin || ['http:', 'https:'].includes(target.protocol)) return target.href;
  return '';
}

function launch(game) {
  const target = gameURL(game);
  if (!game.local) {
    const link = document.createElement('a');
    link.href = target;
    link.target = '_blank';
    link.rel = 'noopener';
    link.click();
    return;
  }
  document.querySelector('#player-title').textContent = game.title;
  document.querySelector('#player-source').textContent = game.source;
  document.querySelector('#open-direct').href = target;
  const sandbox = ['allow-scripts', 'allow-forms', 'allow-modals', 'allow-pointer-lock', 'allow-popups', 'allow-downloads'];
  frame.setAttribute('sandbox', sandbox.join(' '));
  frame.src = target;
  dialog.showModal();
}

function visibleGames() {
  const query = state.query.toLowerCase();
  return state.games.filter(game => {
    if (state.source !== 'All' && game.source !== state.source) return false;
    if (!query) return true;
    return `${game.title} ${game.description} ${game.category} ${game.source} ${(game.tags || []).join(' ')}`
      .toLowerCase().includes(query);
  });
}

function render() {
  const games = visibleGames();
  const displayedGames = games.slice(0, state.visibleLimit);
  const fragment = document.createDocumentFragment();
  for (const game of displayedGames) {
    const card = template.content.firstElementChild.cloneNode(true);
    const button = card.querySelector('.game-launch');
    const image = card.querySelector('img');
    const fallback = card.querySelector('.fallback');
    button.setAttribute('aria-label', `Play ${game.title} from ${game.source}`);
    button.addEventListener('click', () => launch(game));
    card.querySelector('.source').textContent = game.source;
    card.querySelector('.title').textContent = game.title;
    card.querySelector('.category').textContent = game.category;
    fallback.textContent = initials(game.title);
    if (game.image) {
      image.src = imageURL(game.image);
      image.addEventListener('load', () => card.classList.add('image-loaded'), { once: true });
      image.addEventListener('error', () => image.remove(), { once: true });
    } else {
      image.remove();
    }
    fragment.append(card);
  }
  grid.replaceChildren(fragment);
  count.textContent = games.length === displayedGames.length
    ? `${games.length} shown`
    : `${displayedGames.length} of ${games.length} shown`;
  empty.hidden = games.length !== 0;
  showMore.hidden = displayedGames.length === games.length;
}

function resetAndRender() {
  state.visibleLimit = PAGE_SIZE;
  render();
}

function renderFilters() {
  const sourceCounts = new Map();
  for (const game of state.games) sourceCounts.set(game.source, (sourceCounts.get(game.source) || 0) + 1);
  const sources = ['All', ...[...sourceCounts.keys()].sort((a, b) => a.localeCompare(b))];
  filters.replaceChildren(...sources.map(source => {
    const button = document.createElement('button');
    button.type = 'button';
    button.textContent = source === 'All' ? `All ${state.games.length}` : `${source} ${sourceCounts.get(source)}`;
    button.className = source === state.source ? 'active' : '';
    button.addEventListener('click', () => {
      state.source = source;
      renderFilters();
      resetAndRender();
    });
    return button;
  }));
}

search.addEventListener('input', () => {
  state.query = search.value.trim();
  resetAndRender();
});
showMore.addEventListener('click', () => {
  state.visibleLimit += PAGE_SIZE;
  render();
});
document.querySelector('#close-player').addEventListener('click', () => dialog.close());
document.querySelector('#fullscreen').addEventListener('click', () => frame.requestFullscreen?.());
dialog.addEventListener('close', () => { frame.src = 'about:blank'; });
dialog.addEventListener('cancel', event => { event.preventDefault(); dialog.close(); });
dialog.addEventListener('click', event => { if (event.target === dialog) dialog.close(); });
document.querySelector('#year').textContent = new Date().getFullYear();

fetch('catalog.json')
  .then(response => {
    if (!response.ok) throw new Error(`Catalog request failed: ${response.status}`);
    return response.json();
  })
  .then(games => {
    state.games = games;
    document.querySelector('#summary').textContent = `${games.length} games · ${new Set(games.map(game => game.source)).size} sources`;
    renderFilters();
    render();
  })
  .catch(error => {
    document.querySelector('#summary').textContent = 'Catalog failed to load';
    empty.hidden = false;
    empty.textContent = error.message;
  });

if ('serviceWorker' in navigator && location.protocol === 'https:') navigator.serviceWorker.register('sw.js');
