#!/usr/bin/env node
'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

function element(name = '') {
  return {
    name,
    children: [],
    hidden: false,
    value: '',
    textContent: '',
    className: '',
    href: '',
    src: '',
    listeners: {},
    attributes: {},
    classList: { add() {} },
    setAttribute(key, value) { this.attributes[key] = value; },
    addEventListener(type, handler) { this.listeners[type] = handler; },
    replaceChildren(...children) { this.children = children; },
    append(child) { this.children.push(child); },
    remove() { this.removed = true; },
    click() { this.clicked = true; this.listeners.click?.({ target: this }); },
    close() { this.closed = true; this.listeners.close?.({ target: this }); },
    showModal() { this.opened = true; },
    requestFullscreen() { this.fullscreen = true; },
  };
}

function card() {
  const parts = Object.fromEntries(
    ['.game-launch', 'img', '.fallback', '.source', '.title', '.category'].map(selector => [selector, element(selector)]),
  );
  return {
    parts,
    classList: { add() {} },
    querySelector(selector) { return parts[selector]; },
  };
}

const elements = Object.fromEntries(
  ['#game-grid', '#game-count', '#empty-state', '#source-filters', '#search', '#player', '#game-frame',
   '#show-more', '#player-title', '#player-source', '#open-direct', '#close-player', '#fullscreen', '#year', '#summary',
   '#card-template']
    .map(selector => [selector, element(selector)]),
);
const createdLinks = [];
const document = {
  querySelector(selector) { return elements[selector]; },
  createDocumentFragment() { return element('fragment'); },
  createElement(tag) {
    const node = element(tag);
    if (tag === 'a') createdLinks.push(node);
    return node;
  },
};
document.querySelector('#card-template').content = {
  firstElementChild: { cloneNode() { return card(); } },
};

const games = Array.from({ length: 150 }, (_, index) => ({
  id: `game-${index}`,
  title: `Game ${index}`,
  description: index === 149 ? 'needle' : '',
  category: 'Arcade',
  tags: [],
  source: index % 2 ? 'Remote' : 'Local',
  url: index % 2 ? `https://example.com/${index}` : `games/${index}.html`,
  image: '',
  local: index % 2 === 0,
}));

const context = {
  console,
  document,
  fetch: async () => ({ ok: true, json: async () => games }),
  location: { protocol: 'http:', href: 'http://localhost/', origin: 'http://localhost' },
  navigator: {},
  setTimeout,
  URL,
};
vm.runInNewContext(fs.readFileSync('app.js', 'utf8'), context, { filename: 'app.js' });

setImmediate(() => {
  assert.equal(elements['#game-grid'].children[0].children.length, 96);
  assert.equal(elements['#game-count'].textContent, '96 of 150 shown');
  assert.equal(elements['#show-more'].hidden, false);

  elements['#show-more'].click();
  assert.equal(elements['#game-grid'].children[0].children.length, 150);
  assert.equal(elements['#game-count'].textContent, '150 shown');
  assert.equal(elements['#show-more'].hidden, true);

  elements['#search'].value = 'needle';
  elements['#search'].listeners.input();
  assert.equal(elements['#game-grid'].children[0].children.length, 1);
  assert.equal(elements['#game-count'].textContent, '1 shown');

  elements['#search'].value = '';
  elements['#search'].listeners.input();
  const remoteCard = elements['#game-grid'].children[0].children[1];
  remoteCard.parts['.game-launch'].click();
  assert.equal(createdLinks.length, 1);
  assert.equal(createdLinks[0].href, 'https://example.com/1');
  assert.equal(createdLinks[0].clicked, true);
  assert.equal(elements['#player'].opened, undefined);

  const localCard = elements['#game-grid'].children[0].children[0];
  localCard.parts['.game-launch'].click();
  assert.equal(elements['#player'].opened, true);
  assert.equal(elements['#game-frame'].src, 'http://localhost/games/0.html');
  assert.equal(elements['#game-frame'].attributes.sandbox.includes('allow-same-origin'), false);

  assert.throws(
    () => context.gameURL({ id: 'unsafe', local: false, url: 'javascript:alert(1)' }),
    /Unsafe game URL/,
  );
  context.launch({
    id: 'terraria-wasm',
    title: 'Terraria',
    source: 'terraria-wasm',
    url: 'games/terraria/index.html',
    local: true,
  });
  assert.equal(elements['#game-frame'].attributes.sandbox.includes('allow-same-origin'), true);

  console.log(JSON.stringify({
    result: 'PASS',
    initialCards: 96,
    expandedCards: 150,
    searchMatches: 1,
    unsafeURLRejected: true,
    localGameSandboxed: true,
  }));
});
