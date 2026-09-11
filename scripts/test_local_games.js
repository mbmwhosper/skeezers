#!/usr/bin/env node
'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

function inlineScript(path) {
  const html = fs.readFileSync(path, 'utf8');
  const scripts = [...html.matchAll(/<script[^>]*>([\s\S]*?)<\/script>/gi)];
  assert.equal(scripts.length, 1, `${path} should have one inline script`);
  return scripts[0][1];
}

const clickNodes = {
  'score-text': { innerText: '0' },
  'click-button': { addEventListener(type, handler) { assert.equal(type, 'click'); this.handler = handler; } },
};
vm.runInNewContext(inlineScript('games/gogoat/Click-Me.html'), {
  document: { getElementById(id) { return clickNodes[id]; } },
});
clickNodes['click-button'].handler();
assert.equal(clickNodes['score-text'].innerText, 1);

const result = { innerHTML: '' };
const confetti = { appendChild() {}, innerHTML: '' };
const rockDocument = {
  getElementById(id) { return id === 'result' ? result : confetti; },
  createElement() { return { classList: { add() {} }, style: {} }; },
};
const rockContext = {
  document: rockDocument,
  Math: Object.create(Math, { random: { value: () => 0.5 } }),
  setTimeout(handler) { handler(); },
};
vm.createContext(rockContext);
vm.runInContext(inlineScript('games/gogoat/RockPaperScissors.html'), rockContext);
rockContext.play('rock');
assert.match(result.innerHTML, /You chose rock\. Computer chose paper\. Computer wins!/);

console.log(JSON.stringify({ result: 'PASS', clickerIncremented: true, rockPaperScissorsRound: true }));
