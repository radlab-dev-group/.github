const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const source = fs.readFileSync(path.join(__dirname, '../theme/assets/js/consent.js'), 'utf8');
const key = 'radlab-analytics-consent';
const code = 'G-6NPWS2TQEC';
const saved = (choice, time = Date.now()) => JSON.stringify({ version: 1, choice, time });

function setup({ stored = null, blocked = false, enabled = true } = {}) {
  const scripts = [], cookieWrites = [], events = {};
  let reloads = 0, focused, focusOptions;
  const button = choice => ({
    getAttribute() { return choice; },
    addEventListener(name, fn) { this[name] = fn; },
    focus(options) { focused = choice; focusOptions = options; },
  });
  const reject = button('denied'), accept = button('granted'), settings = button('settings');
  const panel = {
    hidden: true, getAttribute() { return code; },
    querySelectorAll() { return [reject, accept]; }, querySelector() { return reject; },
  };
  const document = {
    getElementById() { return enabled ? panel : null; }, querySelector() { return settings; },
    createElement() { return {}; }, head: { appendChild(script) { scripts.push(script); } },
    get cookie() { if (blocked) throw Error('Blocked'); return '_ga=old; _ga_6NPWS2TQEC=old; unrelated=keep'; },
    set cookie(value) { cookieWrites.push(value); },
  };
  const window = {
    location: { hostname: 'www.radlab.dev', pathname: '/preview/en/blog/', reload() { reloads++; } },
    addEventListener(name, fn) { events[name] = fn; },
  };
  const storage = {
    getItem() { if (blocked) throw Error('Blocked'); return stored; },
    setItem(name, value) { if (blocked) throw Error('Blocked'); assert.equal(name, key); stored = value; },
  };
  vm.runInNewContext(source, { document, window, localStorage: storage });
  return { scripts, panel, reject, accept, settings, window, cookieWrites,
    stored: () => stored, reloads: () => reloads, focused: () => focused,
    focusOptions: () => focusOptions,
    external(value, eventKey = key) { stored = value; events.storage({ key: eventKey }); } };
}

test('no consent means no Google script or data layer; refusal is remembered', () => {
  const state = setup();
  assert.equal(state.panel.hidden, false);
  assert.equal(state.scripts.length, 0);
  assert.equal(state.window.dataLayer, undefined);
  state.reject.click();
  assert.equal(state.panel.hidden, true);
  assert.equal(JSON.parse(state.stored()).choice, 'denied');
  assert.equal(state.scripts.length, 0);
  assert.equal(state.reloads(), 0);
  assert.equal(setup({ stored: state.stored() }).panel.hidden, true);
});

test('acceptance loads GA once, disables ads, and persists across pages', () => {
  const state = setup();
  state.accept.click();
  state.accept.click();
  assert.equal(state.scripts.length, 1);
  assert.equal(state.scripts[0].src, `https://www.googletagmanager.com/gtag/js?id=${code}`);
  assert.equal(state.window['ga-disable-' + code], false);
  const commands = state.window.dataLayer.map(args => Array.from(args));
  assert.equal(commands[0][0], 'consent');
  assert.equal(commands[0][2].analytics_storage, 'granted');
  assert.equal(commands[0][2].ad_storage, 'denied');
  assert.equal(commands[0][2].ad_user_data, 'denied');
  assert.equal(commands[0][2].ad_personalization, 'denied');
  assert.equal(commands[2][2].allow_google_signals, false);
  assert.equal(JSON.parse(state.stored()).choice, 'granted');
  assert.equal(setup({ stored: state.stored() }).scripts.length, 1);
});

test('footer reopens settings; withdrawal disables GA, clears cookies and reloads', () => {
  const state = setup({ stored: saved('granted') });
  state.settings.click();
  assert.equal(state.panel.hidden, false);
  assert.equal(state.focused(), 'denied');
  state.reject.click();
  assert.equal(state.window['ga-disable-' + code], true);
  assert.equal(state.reloads(), 1);
  assert.equal(state.focused(), 'settings');
  assert.equal(JSON.parse(state.stored()).choice, 'denied');
  assert.ok(state.cookieWrites.some(cookie => cookie.includes('domain=radlab.dev')));
  assert.ok(state.cookieWrites.some(cookie => cookie.includes('path=/preview/en/blog/')));
  assert.ok(state.cookieWrites.every(cookie => cookie.startsWith('_ga')));
});

test('a choice hands focus to the footer button without dragging the viewport there', () => {
  const first = setup();
  first.accept.click();
  assert.equal(first.focused(), 'settings');
  assert.equal(first.focusOptions().preventScroll, true);
  const reopened = setup({ stored: saved('granted') });
  reopened.settings.click();
  reopened.reject.click();
  assert.equal(reopened.focused(), 'settings');
  assert.equal(reopened.focusOptions().preventScroll, true);
});

test('expired, malformed, unknown-version and future choices require new consent', () => {
  for (const stored of ['invalid', '{}', saved('other'), saved('granted', Date.now() - 181 * 86400000),
    saved('granted', Date.now() + 86400000), JSON.stringify({ version: 2, choice: 'granted', time: Date.now() })]) {
    const state = setup({ stored });
    assert.equal(state.panel.hidden, false);
    assert.equal(state.scripts.length, 0);
  }
});

test('blocked storage fails closed but still permits an explicit page-only choice', () => {
  const state = setup({ blocked: true });
  assert.equal(state.scripts.length, 0);
  state.accept.click();
  assert.equal(state.scripts.length, 1);
  state.reject.click();
  assert.equal(state.reloads(), 1);
  assert.equal(setup({ blocked: true }).scripts.length, 0);
});

test('consent changes and storage clearing propagate between tabs', () => {
  const state = setup({ stored: saved('denied') });
  state.external(saved('granted'));
  assert.equal(state.scripts.length, 1);
  state.external(saved('denied'));
  assert.equal(state.reloads(), 1);
  const cleared = setup({ stored: saved('granted') });
  cleared.external(null, null);
  assert.equal(cleared.reloads(), 1);
  assert.equal(cleared.panel.hidden, false);
});

test('disabled integration does nothing', () => {
  const state = setup({ enabled: false });
  assert.equal(state.scripts.length, 0);
  assert.equal(state.cookieWrites.length, 0);
});