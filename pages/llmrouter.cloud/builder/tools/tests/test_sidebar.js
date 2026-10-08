const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const source = fs.readFileSync(path.join(__dirname, '../theme/docs.js'), 'utf8');
const sidebarCode = source.slice(source.indexOf('  function initSidebar()'),
  source.indexOf('  /* ---- version switcher'));

function fixture(storage, root = 'https://example.invalid/docs/') {
  const groups = ['router', 'plugins', 'services'].map(repo => {
    const group = {getAttribute() { return repo; }};
    const details = {open: false, closest() { return group; },
      matches(selector) { return selector === 'details.nav-group'; }};
    group.querySelector = () => details;
    return group;
  });
  const handlers = {};
  const window = {location: {href: root + '1.1.0/index.html'}, sessionStorage: storage,
    addEventListener(name, fn) { handlers[name] = fn; }};
  const doc = {addEventListener(name, fn, capture) {
    handlers[name] = fn;
    if (name === 'toggle') assert.equal(capture, true, 'toggle does not bubble');
  }};
  vm.runInNewContext(sidebarCode + '\ninitSidebar();', {
    window, doc, URL, body: {getAttribute() { return root; }}, all() { return groups; },
  });
  return {groups, handlers, details: groups.map(group => group.querySelector())};
}

const values = new Map();
const storage = {getItem(key) { return values.get(key) ?? null; },
  setItem(key, value) { values.set(key, value); }};
const first = fixture(storage);
assert.deepEqual(first.details.map(details => details.open), [false, false, false]);
first.details[0].open = true;
first.handlers.toggle({target: first.details[0]});
first.details[1].open = true;
first.handlers.pagehide();
const documentPage = fixture(storage);
assert.deepEqual(documentPage.details.map(details => details.open), [true, true, false],
  'following a document link must preserve each repository menu');
documentPage.details[0].open = false;
documentPage.handlers.toggle({target: documentPage.details[0]});
const versionPage = fixture(storage);
assert.deepEqual(versionPage.details.map(details => details.open), [false, true, false],
  'version navigation must preserve explicitly collapsed sections too');
assert.deepEqual(fixture(storage, 'https://example.invalid/other/docs/').details.map(d => d.open),
  [false, false, false], 'different documentation sites must not share state');
assert.doesNotThrow(() => fixture({getItem() { throw new Error('blocked'); },
  setItem() { throw new Error('blocked'); }}).handlers.pagehide());
assert.doesNotThrow(() => fixture({getItem() { return '{invalid'; }, setItem() {}}));
console.log('Sidebar navigation state: OK');