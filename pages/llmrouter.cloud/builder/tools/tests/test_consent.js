const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const GA_SAMPLE =
  '<script async src="https://www.googletagmanager.com/gtag/js?id=G-TEST"></scr' +
  'ipt>\n<script>gtag(\'config\',\'G-TEST\');</scr' + 'ipt>';

const source = fs.readFileSync(path.join(__dirname, '../theme/consent.js'), 'utf8');
assert.ok(source.includes('var GA_PAYLOAD = @@GA@@;'), 'consent.js lost its payload token');
const code = source.replace('var GA_PAYLOAD = @@GA@@;',
  'var GA_PAYLOAD = ' + JSON.stringify(GA_SAMPLE) + ';');

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

function DOMParser() {}
DOMParser.prototype.parseFromString = function (payload) {
  const body = element('body');
  body.childNodes = body.children;
  const scripts = /<script([^>]*)>([\s\S]*?)<\/script>/g;
  let match;
  while ((match = scripts.exec(payload))) {
    const script = element('script');
    const src = /src="([^"]*)"/.exec(match[1]);
    if (src) script.setAttribute('src', src[1]);
    script.textContent = match[2];
    body.appendChild(script);
  }
  return {body};
};

function collect(node) {
  return [node, ...node.children.flatMap(collect)];
}

function run(stored, privacy = '../../privacy.html') {
  const values = new Map(stored === null ? [] : [['llmrouter.analytics.consent.v1', stored]]);
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
  vm.runInNewContext(code, {window, document: doc, DOMParser, JSON, Date, Array, Object, String});
  const api = {
    window,
    values,
    handlers,
    panel: () => find(body, 'llmrc-panel'),
    scripts: () => head.children.filter(node => node.tagName === 'SCRIPT'),
    state: () => (values.size ? JSON.parse(values.get('llmrouter.analytics.consent.v1')).state : ''),
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
assert.deepEqual(choices, ['granted', 'denied', 'later']);
const link = collect(panel).find(node => node.tagName === 'A');
assert.equal(link.href, '../../privacy.html');

/* ---- accept: the decision is stored and the payload is injected ------- */
fresh.choice('granted');
assert.equal(fresh.state(), 'granted');
assert.equal(fresh.panel(), null, 'panel stays open after a decision');
assert.deepEqual(fresh.scripts().map(node => node.getAttribute('src') || ''),
  ['https://www.googletagmanager.com/gtag/js?id=G-TEST', '']);

/* ---- declined: never loads, never asks again -------------------------- */
const declined = run(JSON.stringify({state: 'denied'}));
assert.equal(declined.panel(), null, 'a stored decision asks again');
assert.equal(declined.scripts().length, 0, 'analytics loaded after a refusal');

/* ---- accepted earlier: loads straight away, no panel ------------------ */
const accepted = run(JSON.stringify({state: 'granted'}));
assert.equal(accepted.panel(), null);
assert.equal(accepted.scripts().length, 2);

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

console.log('consent gate ok');
