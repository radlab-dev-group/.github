const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const GA_SAMPLE =
  '<script async src="https://www.googletagmanager.com/gtag/js?id=G-TEST"></scr' +
  'ipt>\n<script>gtag(\'config\',\'G-TEST\');</scr' + 'ipt>';

const source = fs.readFileSync(path.join(__dirname, '../theme/consent.js'), 'utf8');
assert.ok(source.includes('var GA_PAYLOAD = @@GA@@;'), 'consent.js lost its payload token');
const KEY = 'llmrouter.analytics.consent.v1';
const DAY = 24 * 60 * 60 * 1000;
const BASE_TIME = Date.UTC(2026, 0, 1, 12, 0, 0);

function codeFor(payload, loadWithoutConsent) {
  const rendered = source.replace('var GA_PAYLOAD = @@GA@@;',
    'var GA_PAYLOAD = ' + JSON.stringify(payload) + ';');
  if (!loadWithoutConsent) {
    return rendered;
  }
  assert.ok(rendered.includes('var LOAD_WITHOUT_CONSENT = false;'),
    'consent.js lost its LOAD_WITHOUT_CONSENT flag');
  return rendered.replace('var LOAD_WITHOUT_CONSENT = false;',
    'var LOAD_WITHOUT_CONSENT = true;');
}

const code = codeFor(GA_SAMPLE);

function matches(node, selector) {
  if (selector === '[data-consent-open]') return node.getAttribute('data-consent-open') !== null;
  if (selector === '[data-choice]') return node.getAttribute('data-choice') !== null;
  return false;
}

function element(tag) {
  const node = {
    tagName: String(tag).toUpperCase(),
    nodeType: 1,
    attributes: [],
    children: [],
    parentNode: null,
    id: '',
    className: '',
    innerHTML: '',
    textContent: '',
    setAttribute(name, value) {
      this.attributes.push({name, value: String(value)});
      if (name === 'id') this.id = String(value);
    },
    getAttribute(name) {
      const found = this.attributes.find(attr => attr.name === name);
      return found ? found.value : null;
    },
    appendChild(child) {
      child.parentNode = this;
      this.children.push(child);
      return child;
    },
    removeChild(child) {
      this.children = this.children.filter(item => item !== child);
      child.parentNode = null;
      return child;
    },
    focus() {
      this.focused = (this.focused || 0) + 1;
    },
    closest(selector) {
      let current = this;
      while (current) {
        if (current.getAttribute && matches(current, selector)) return current;
        current = current.parentNode;
      }
      return null;
    },
  };
  return node;
}

function find(node, id) {
  if (node.id === id) return node;
  for (const child of node.children) {
    const found = find(child, id);
    if (found) return found;
  }
  return null;
}

/* A real browser parsing a snippet as text/html hoists <script>, <link> and
   <meta> into <head>; only other elements stay in <body>. The mock follows the
   same rule, otherwise the loader could pass by relying on the wrong root. */
const HEAD_ONLY = /^(script|link|meta|title)$/;

function DOMParser() {}
DOMParser.prototype.parseFromString = function (payload) {
  const head = element('head');
  const body = element('body');
  head.childNodes = head.children;
  body.childNodes = body.children;
  const tags = /<(script|link|meta|title|noscript)([^>]*)>([\s\S]*?)<\/\1>/g;
  let match;
  while ((match = tags.exec(payload))) {
    const node = element(match[1]);
    const src = /src="([^"]*)"/.exec(match[2]);
    if (src) node.setAttribute('src', src[1]);
    node.textContent = match[3];
    (HEAD_ONLY.test(match[1]) ? head : body).appendChild(node);
  }
  return {head, body};
};

function collect(node) {
  return [node, ...node.children.flatMap(collect)];
}

function run(stored, privacy = '../../privacy.html', options = {}) {
  const clock = {now: options.now === undefined ? BASE_TIME : options.now};
  const values = new Map(stored === null ? [] : [[KEY, stored]]);
  const head = element('head');
  const body = element('body');
  const handlers = {};
  const currentScript = {getAttribute: name => (name === 'data-privacy' ? privacy : null)};
  const window = {
    localStorage: {
      getItem: key => (values.has(key) ? values.get(key) : null),
      setItem: (key, value) => values.set(key, value),
    },
  };
  const doc = {
    head,
    body,
    currentScript,
    createElement: tag => element(tag),
    getElementById: id => find(head, id) || find(body, id),
    importNode: node => node,
    addEventListener: (name, fn) => { handlers[name] = fn; },
  };
  vm.runInNewContext(options.code || code, {
    window, document: doc, DOMParser, JSON, Array, Object, String,
    Date: {now: () => clock.now},
  });
  const api = {
    window,
    values,
    clock,
    handlers,
    panel: () => find(body, 'llmrc-panel'),
    scripts: () => head.children.filter(node => node.tagName === 'SCRIPT'),
    record: () => JSON.parse(values.get(KEY)),
    state: () => (values.size ? JSON.parse(values.get(KEY)).state : ''),
  };
  api.choice = choice => {
    const buttons = collect(find(body, 'llmrc-panel'))
      .filter(node => node.getAttribute && node.getAttribute('data-choice') === choice);
    assert.equal(buttons.length, 1, 'button for ' + choice);
    handlers.click({target: buttons[0]});
  };
  return api;
}

/* ---- first visit: the panel asks, nothing is loaded ------------------- */
const fresh = run(null);
const panel = fresh.panel();
assert.ok(panel, 'no consent panel on a first visit');
assert.equal(panel.getAttribute('role'), 'dialog');
assert.equal(fresh.scripts().length, 0, 'analytics loaded before consent');
const choices = collect(panel).filter(node => node.getAttribute && node.getAttribute('data-choice') !== null)
  .map(node => node.getAttribute('data-choice'));
assert.deepEqual(choices, ['granted', 'denied', 'postponed']);
const link = collect(panel).find(node => node.tagName === 'A');
assert.equal(link.href, '../../privacy.html');

/* ---- accept: the decision is stored and the payload is injected ------- */
fresh.choice('granted');
assert.equal(fresh.state(), 'granted');
assert.equal(fresh.panel(), null, 'panel stays open after a decision');
assert.deepEqual(fresh.scripts().map(node => node.getAttribute('src') || ''),
  ['', 'https://www.googletagmanager.com/gtag/js?id=G-TEST', '']);

/* Consent Mode v2: analytics is granted, the advertising categories are not */
const defaults = fresh.scripts()[0].textContent;
assert.ok(defaults.includes("gtag('consent','default'"), 'no consent defaults');
assert.ok(defaults.includes("'analytics_storage':'granted'"), 'analytics not granted');
['ad_storage', 'ad_user_data', 'ad_personalization'].forEach(name => {
  assert.ok(defaults.includes("'" + name + "':'denied'"), name + ' should stay denied');
});

/* ---- declined: never loads, never asks again -------------------------- */
const declined = run(JSON.stringify({state: 'denied'}));
assert.equal(declined.panel(), null, 'a stored decision asks again');
assert.equal(declined.scripts().length, 0, 'analytics loaded after a refusal');

/* ---- accepted earlier: loads straight away, no panel ------------------ */
const accepted = run(JSON.stringify({state: 'granted'}));
assert.equal(accepted.panel(), null);
assert.equal(accepted.scripts().length, 3);

/* ---- footer links reopen the panel without changing the decision ------ */
const trigger = element('a');
trigger.setAttribute('data-consent-open', '');
declined.handlers.click({target: trigger, preventDefault() {}});
assert.ok(declined.panel(), 'data-consent-open does not reopen the panel');
assert.equal(declined.state(), 'denied');

/* ---- escape closes the panel and leaves the choice undecided ---------- */
const visitor = run(null);
visitor.handlers.keydown({key: 'Escape'});
assert.equal(visitor.panel(), null);
assert.equal(visitor.state(), '');
assert.equal(visitor.window.llmRouterConsent.state(), '');
visitor.window.llmRouterConsent.decide('denied');
assert.equal(visitor.state(), 'denied');

/* ---- a payload that spans both parsed roots is injected in order --------- */
const MIXED_SAMPLE =
  '<script src="https://www.googletagmanager.com/gtag/js?id=G-MIX"></scr' + 'ipt>\n' +
  '<noscript><img src="https://www.example.com/collect"></noscript>';
const mixedCode = source.replace('var GA_PAYLOAD = @@GA@@;',
  'var GA_PAYLOAD = ' + JSON.stringify(MIXED_SAMPLE) + ';');
(function mixedRoots() {
  const values = new Map();
  const head = element('head');
  const body = element('body');
  const window = {localStorage: {
    getItem: () => JSON.stringify({state: 'granted'}),
    setItem: (key, value) => values.set(key, value),
  }};
  const doc = {
    head, body, currentScript: null,
    createElement: tag => element(tag),
    getElementById: id => find(head, id) || find(body, id),
    importNode: node => node,
    addEventListener: () => {},
  };
  vm.runInNewContext(mixedCode, {
    window, document: doc, DOMParser, JSON, Array, Object, String,
    Date: {now: () => BASE_TIME},
  });
  const loaded = head.children.filter(node => node.tagName !== 'STYLE' &&
    !node.textContent.includes("gtag('consent','default'"));
  assert.equal(loaded.length, 2, 'a head/body split payload is not injected');
  assert.equal(loaded[0].getAttribute('src'),
    'https://www.googletagmanager.com/gtag/js?id=G-MIX');
  assert.equal(loaded[1].tagName, 'NOSCRIPT', 'the body-root node was dropped');
})();

/* ---- "decide later": stored, silent, and it expires ------------------- */
const later = run(null);
later.choice('postponed');
assert.equal(later.state(), 'postponed');
assert.equal(later.scripts().length, 0, 'a postponed choice loaded analytics');
assert.equal(later.panel(), null, 'the panel stayed open after postponing');
assert.equal(later.record().until, BASE_TIME + 30 * DAY, 'quiet period is not 30 days');

const postponed = JSON.stringify(later.record());
const quiet = run(postponed, '../../privacy.html', {now: BASE_TIME + 29 * DAY});
assert.equal(quiet.panel(), null, 'the panel nags during the quiet period');
assert.equal(quiet.scripts().length, 0, 'analytics loaded while postponed');

const elapsed = run(postponed, '../../privacy.html', {now: BASE_TIME + 31 * DAY});
assert.ok(elapsed.panel(), 'the panel does not return once the quiet period ends');
assert.equal(elapsed.scripts().length, 0, 'analytics loaded before a fresh choice');
elapsed.choice('granted');
assert.equal(elapsed.state(), 'granted');
assert.equal(elapsed.scripts().length, 3, 'the payload did not follow the fresh yes');

/* ---- optional consent-state pings for visitors who never accept ------- */
const pings = run(null, '../../privacy.html', {code: codeFor(GA_SAMPLE, true)});
assert.ok(pings.panel(), 'the panel must still ask when pings are enabled');
assert.equal(pings.scripts().length, 3, 'the denied-state payload was not loaded');
assert.ok(pings.scripts()[0].textContent.includes("'analytics_storage':'denied'"),
  'analytics must default to denied without a choice');
pings.choice('granted');
const updates = pings.scripts().slice(3).map(node => node.textContent);
assert.deepEqual(updates, ["gtag('consent','update',{'analytics_storage':'granted'});"]);
assert.equal(pings.scripts().length, 4, 'the payload was injected twice');

console.log('consent gate ok');
