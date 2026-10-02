const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const source = fs.readFileSync(path.join(__dirname, '../static/js/site.js'), 'utf8');

function setup({ secure = true, clipboard = true, reject = false } = {}) {
  const created = [];
  const writes = [];
  const code = { textContent: 'print("Zażółć <tag>")\n' };
  const pre = { parentNode: { insertBefore() {} } };
  code.parentNode = pre;
  const labels = { copyCode: 'Kopiuj kod', codeCopied: 'Skopiowano', copyFailed: 'Błąd kopiowania' };
  const document = {
    documentElement: {
      classList: { add() {} },
      getAttribute() { return 'light'; },
      setAttribute() {},
    },
    body: { dataset: labels },
    addEventListener() {},
    querySelector() { return null; },
    querySelectorAll(selector) { return selector === '.prose pre > code' ? [code] : []; },
    createElement(tag) {
      const element = {
        tag, children: [],
        appendChild(child) { this.children.push(child); },
        setAttribute(name, value) { this[name] = value; },
        addEventListener(name, handler) { this[name] = handler; },
      };
      created.push(element);
      return element;
    },
  };
  const navigator = clipboard ? {
    clipboard: {
      writeText(text) {
        writes.push(text);
        return reject ? Promise.reject(new Error('Permission denied')) : Promise.resolve();
      },
    },
  } : {};
  vm.runInNewContext(source, {
    document, navigator,
    window: {
      isSecureContext: secure,
      matchMedia() { return { matches: true, addEventListener() {} }; },
      addEventListener() {},
    },
  });
  return { created, writes, code, pre, labels };
}

test('copy works with reduced motion and copies only the exact code text', async () => {
  const { created, writes, code, pre, labels } = setup();
  const [wrapper, button, status] = created;
  assert.equal(wrapper.children[0], pre);
  assert.equal(button.type, 'button');
  assert.equal(button.textContent, labels.copyCode);
  assert.equal(status.role, 'status');
  button.click();
  assert.equal(button.disabled, true);
  await Promise.resolve();
  assert.deepEqual(writes, [code.textContent]);
  assert.equal(status.textContent, labels.codeCopied);
  assert.equal(button.disabled, false);
});

test('clipboard rejection gives feedback and allows retry', async () => {
  const { created, labels } = setup({ reject: true });
  const [, button, status] = created;
  button.click();
  await Promise.resolve();
  assert.equal(status.textContent, labels.copyFailed);
  assert.equal(button.disabled, false);
});

test('missing clipboard leaves code unchanged', () => {
  assert.equal(setup({ clipboard: false }).created.length, 0);
});

test('insecure context leaves code unchanged', () => {
  assert.equal(setup({ secure: false }).created.length, 0);
});