const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const sourcePath = path.join(__dirname, '../theme/assets/js/preferences.js');

function setup({ languages = ['en-GB'], stored = {}, dark = false, blocked = false,
                 lang = 'pl', auto = true, pathname = '/preview/' } = {}) {
  const attributes = {
    lang, 'data-default-lang': 'pl', 'data-language-auto': String(auto),
    'data-language-pl': '/preview/', 'data-language-en': '/preview/en/',
  };
  const redirects = [];
  const handlers = {};
  const root = {
    classList: { add() {} },
    getAttribute(name) { return attributes[name] || null; },
    setAttribute(name, value) { attributes[name] = value; },
  };
  const media = { matches: dark, addEventListener(name, fn) { handlers.change = fn; } };
  vm.runInNewContext(fs.readFileSync(sourcePath, 'utf8'), {
    document: {
      documentElement: root, querySelectorAll() { return []; },
      addEventListener(name, fn) { handlers[name] = fn; },
    },
    navigator: { languages },
    localStorage: {
      getItem(key) { if (blocked) throw new Error('Denied'); return stored[key]; },
      setItem(key, value) { if (blocked) throw new Error('Denied'); stored[key] = value; },
    },
    window: {
      matchMedia() { return media; },
      location: { pathname, search: '?utm_source=test', hash: '#contact',
        replace(url) { redirects.push(url); } },
    },
  });
  return { attributes, redirects, handlers, stored };
}

test('browser languages select a supported home and preserve query/hash', () => {
  assert.deepEqual(setup({ languages: ['de-DE', 'en-US', 'pl'] }).redirects,
    ['/preview/en/?utm_source=test#contact']);
  assert.deepEqual(setup({ languages: ['pl-PL', 'en'] }).redirects, []);
  assert.deepEqual(setup({ languages: ['de'] }).redirects, []);
});

test('manual language choice wins and article links are not redirected', () => {
  assert.deepEqual(setup({ stored: { 'radlab-language': 'pl' } }).redirects, []);
  assert.deepEqual(setup({ auto: false }).redirects, []);
  const state = setup({ auto: false });
  state.handlers.click({ target: { closest(selector) {
    return selector === '.lang-switch' ? { getAttribute() { return 'en'; } } : null;
  } } });
  assert.equal(state.stored['radlab-language'], 'en');
});

test('system theme follows live changes unless explicitly overridden', () => {
  const state = setup({ dark: true });
  assert.equal(state.attributes['data-theme'], 'dark');
  state.handlers.change({ matches: false });
  assert.equal(state.attributes['data-theme'], 'light');
  state.handlers.click({ target: { closest(selector) {
    return selector === '.theme-toggle' ? {} : null;
  } } });
  state.handlers.change({ matches: false });
  assert.equal(state.attributes['data-theme'], 'dark');
  assert.equal(state.stored['radlab-theme'], 'dark');
  assert.equal(setup({ dark: true, stored: { 'radlab-theme': 'light' } }).attributes['data-theme'], 'light');
});

test('blocked storage and invalid saved values do not break system preferences', () => {
  const state = setup({ blocked: true, dark: true });
  assert.equal(state.attributes['data-theme'], 'dark');
  assert.equal(state.redirects.length, 1);
  assert.equal(setup({ dark: true, stored: { 'radlab-theme': 'invalid' } }).attributes['data-theme'], 'dark');
});