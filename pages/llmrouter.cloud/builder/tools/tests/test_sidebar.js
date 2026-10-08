const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const source = fs.readFileSync(path.join(__dirname, '../theme/docs.js'), 'utf8');
const sidebarCode = source.slice(source.indexOf('  function initSidebar()'),
  source.indexOf('  /* ---- version switcher'));

function fixture(storage, root = 'https://example.invalid/docs/', query = '', active = '') {
  const groups = ['router', 'plugins', 'services'].map(repo => {
    const group = {getAttribute() { return repo; }};
    const details = {open: false, closest() { return group; },
      matches(selector) { return selector === 'details.nav-group'; }};
    group.querySelector = selector => selector === 'details.nav-group' ? details :
      (selector === '.nav-sec li a.active' && repo === active ? {className: 'active'} : null);
    return group;
  });
  const handlers = {};
  const window = {location: {href: root + '1.1.0/index.html' + query}, sessionStorage: storage,
    addEventListener(name, fn) { handlers[name] = fn; }};
  const doc = {addEventListener(name, fn, capture) {
    handlers[name] = fn;
    if (name === 'toggle') assert.equal(capture, true, 'toggle does not bubble');
  }};
  vm.runInNewContext(sidebarCode + '\ninitSidebar();', {
    window, doc, URL, body: {getAttribute() { return root; }}, all() { return groups; },
  });
  return {groups, handlers, details: groups.map(group => group.querySelector('details.nav-group'))};
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
for (const repo of ['router', 'plugins', 'services']) {
  const isolated = new Map();
  const stored = {getItem(key) { return isolated.get(key) ?? null; },
    setItem(key, value) { isolated.set(key, value); }};
  const result = fixture(stored, undefined, '?reveal=search', repo);
  assert.equal(result.groups.find(group => group.getAttribute() === repo)
    .querySelector('details.nav-group').open, true,
  'search navigation must reveal the active document repository');
  assert.deepEqual(fixture(stored).details.map(d => d.open),
    ['router', 'plugins', 'services'].map(name => name === repo),
    'revealed menu must stay expanded on subsequent navigation');
  assert.deepEqual(fixture({getItem() { return null; }, setItem() {}}, undefined, '', repo)
    .details.map(d => d.open), [false, false, false],
    'ordinary document navigation must not force a section open');
}
assert.equal(fixture({getItem() { throw new Error('blocked'); },
  setItem() { throw new Error('blocked'); }}, undefined, '?reveal=search', 'plugins')
  .details[1].open, true, 'search reveal must work without storage');
console.log('Sidebar navigation state: OK');