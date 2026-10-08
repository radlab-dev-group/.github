const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const source = fs.readFileSync(path.join(__dirname, '../theme/docs.js'), 'utf8');
const searchCode = source.slice(source.indexOf('  function initSearch()'),
  source.indexOf('  function init()'));

async function fixture(indexUrl) {
  function element() {
    return {handlers: {}, value: 'guide', classList: {add() {}, remove() {}},
      addEventListener(name, fn) { this.handlers[name] = fn; },
      setAttribute() {}, querySelector() { return null; }};
  }
  const form = element();
  const input = element();
  const box = element();
  const window = {location: {href: 'https://example.invalid/sub/docs/1.1.0/index.html'}};
  const doc = {getElementById(id) { return {search: form, q: input, results: box}[id]; },
    addEventListener() {}};
  vm.runInNewContext(searchCode + '\ninitSearch();', {
    doc, window, URL, body: {getAttribute() { return indexUrl; }},
    text(value) { return String(value == null ? '' : value); },
    escapeHtml(value) { return String(value).replace(/&/g, '&amp;').replace(/"/g, '&quot;'); },
    fetch() { return Promise.resolve({ok: true, json() {
      return Promise.resolve({pages: [{k: 'guides/guide.html', t: 'Guide', s: 'Guides', b: ''}]});
    }}); },
  });
  input.handlers.input();
  await new Promise(resolve => setImmediate(resolve));
  return {form, input, box, window};
}

(async () => {
  for (const indexUrl of ['search.json', '../plugins/search.json', '../services/0.4.0/search.json']) {
    const result = await fixture(indexUrl);
    const href = result.box.innerHTML.match(/href="([^"]+)"/)[1].replace(/&amp;/g, '&');
    const url = new URL(href, result.window.location.href);
    assert.equal(url.searchParams.get('reveal'), 'search',
      'clicked search result must request sidebar reveal');
    assert.equal(url.pathname, new URL(indexUrl.replace('search.json', 'guides/guide.html'),
      result.window.location.href).pathname);
    for (const keyboardSelection of [false, true]) {
      result.window.location.href = 'https://example.invalid/sub/docs/1.1.0/index.html';
      if (keyboardSelection) result.input.handlers.keydown({key: 'ArrowDown', preventDefault() {}});
      result.form.handlers.submit({preventDefault() {}});
      assert.equal(new URL(result.window.location.href).href, url.href,
        'Enter must open the same document and reveal its menu');
    }
  }
  console.log('Search navigation reveal: OK');
})().catch(error => { console.error(error); process.exitCode = 1; });