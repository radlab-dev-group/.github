/* Browser smoke test: node tools/tests/test_landing.js [--screenshots]
 * Requires Chromium on PATH (or CHROMIUM=/path/to/chromium). No npm dependencies.
 */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {spawn} = require('node:child_process');
const {pathToFileURL} = require('node:url');

const source = fs.readFileSync(path.join(__dirname, '../../landing/index.html'), 'utf8');
const temporary = fs.mkdtempSync(path.join(__dirname, '.landing-test-'));
const preview = path.join(temporary, 'index.html');
fs.writeFileSync(preview, source.replaceAll('{{VERSION}}', '1.2.3').replace('{{GA}}', ''));
const browser = spawn(process.env.CHROMIUM || 'chromium', [
  '--headless', '--no-sandbox', '--disable-gpu', '--no-first-run',
  '--disable-dev-shm-usage', '--remote-debugging-pipe',
  '--user-data-dir=' + path.join(temporary, 'browser'),
], {stdio: ['ignore', 'ignore', 'pipe', 'pipe', 'pipe']});
const closed = new Promise(resolve => browser.once('close', resolve));
let sequence = 0;
let buffer = '';
let diagnostics = '';
const pending = new Map();
const errors = [];
browser.stderr.on('data', data => { diagnostics += data; });
browser.on('error', error => {
  for (const request of pending.values()) request.reject(error);
});
browser.stdio[4].on('data', data => {
  buffer += data;
  let end;
  while ((end = buffer.indexOf('\0')) !== -1) {
    const message = JSON.parse(buffer.slice(0, end));
    buffer = buffer.slice(end + 1);
    if (message.method === 'Runtime.exceptionThrown') errors.push(message.params);
    const request = pending.get(message.id);
    if (request) {
      pending.delete(message.id);
      if (message.error) request.reject(new Error(JSON.stringify(message.error)));
      else request.resolve(message.result);
    }
  }
});

function send(method, params = {}, sessionId) {
  return new Promise((resolve, reject) => {
    const id = ++sequence;
    const timeout = setTimeout(() => {
      pending.delete(id);
      reject(new Error(method + ' timed out: ' + diagnostics));
    }, 15000);
    pending.set(id, {
      resolve: value => { clearTimeout(timeout); resolve(value); },
      reject: error => { clearTimeout(timeout); reject(error); },
    });
    browser.stdio[3].write(JSON.stringify({id, method, params, sessionId}) + '\0');
  });
}

async function main() {
  const {targetId} = await send('Target.createTarget', {url: 'about:blank'});
  const {sessionId} = await send('Target.attachToTarget', {targetId, flatten: true});
  const command = (method, params) => send(method, params, sessionId);
  const evaluate = async expression => {
    const result = await command('Runtime.evaluate', {expression, returnByValue: true, awaitPromise: true});
    assert.equal(result.exceptionDetails, undefined, JSON.stringify(result.exceptionDetails));
    return result.result.value;
  };
  await command('Runtime.enable');
  await command('Page.enable');
  await command('Page.bringToFront');
  await command('Emulation.setEmulatedMedia', {features: [{name: 'prefers-reduced-motion', value: 'reduce'}]});
  for (const width of [1440, 1024, 1001, 1000, 768, 390, 320]) {
    await command('Emulation.setDeviceMetricsOverride', {width, height: 1100, deviceScaleFactor: 1, mobile: false});
    await command('Page.navigate', {url: pathToFileURL(preview).href});
    for (let attempt = 0; attempt < 100; attempt++) {
      if (await evaluate('document.readyState === "complete" && !!document.querySelector(".hero")')) break;
      await new Promise(resolve => setTimeout(resolve, 20));
    }
    const state = await evaluate(`(() => {
      const links = [...document.querySelectorAll('a[href^="#"], use[href^="#"]')];
      const ids = [...document.querySelectorAll('[id]')].map(el => el.id);
      const outside = [...document.querySelectorAll('.nav-inner > *, .nav-right > *, .hero-grid > *, .hero .cta-row > *')]
        .filter(el => getComputedStyle(el).display !== 'none')
        .filter(el => { const r = el.getBoundingClientRect(); return r.left < 0 || r.right > innerWidth + 1; });
      return {
        width: document.documentElement.scrollWidth,
        viewport: innerWidth,
        outside: outside.map(el => el.className),
        navCount: document.querySelectorAll('#navlinks a').length,
        actions: [...document.querySelectorAll('.hero .cta-row a')].map(el => el.getAttribute('href')),
        missing: links.filter(el => !document.getElementById(el.getAttribute('href').slice(1))).map(el => el.getAttribute('href')),
        duplicateIds: ids.filter((id, index) => ids.indexOf(id) !== index),
        hiddenContent: [...document.querySelectorAll('.reveal')].filter(el => getComputedStyle(el).opacity === '0').length,
        animations: document.getAnimations().length
      };
    })()`);
    assert.ok(state.width <= state.viewport, `page overflow at ${width}: ` + await evaluate(`JSON.stringify([...document.querySelectorAll('body *')].filter(el => { const r = el.getBoundingClientRect(); return r.right > innerWidth + 1 && !el.closest('pre, .term-body, .pipe-row, .tbl-wrap, .prom'); }).map(el => [el.tagName, el.className, el.textContent.slice(0, 100), el.parentElement.className]).slice(0, 25))`));
    assert.deepEqual(state.outside, [], `clipped controls at ${width}`);
    assert.equal(state.navCount, 5);
    assert.deepEqual(state.actions, ['docs/#docs-quickstart', 'docs/']);
    assert.deepEqual(state.missing, []);
    assert.deepEqual(state.duplicateIds, []);
    assert.equal(state.hiddenContent, 0);
    assert.equal(state.animations, 0);
    const pipeline = await evaluate(`(() => {
      const nodes = [...document.querySelectorAll('.pipe-flow .node')];
      const rects = nodes.map(el => el.getBoundingClientRect());
      const connectors = [...document.querySelectorAll('.pipe-link')].map(el => el.getBoundingClientRect());
      return {
        groups: [...document.querySelectorAll('.pipe-group h3')].map(el => el.textContent.trim()),
        names: nodes.map(el => el.querySelector('.nm').textContent),
        horizontal: rects.every(r => Math.abs(r.top - rects[0].top) < 1),
        vertical: rects.every((r, i) => !i || (r.top > rects[i - 1].bottom && Math.abs(r.left - rects[0].left) < 1)),
        clipped: [...document.querySelectorAll('.pipe-flow, .node .nm, .node .ds, .node .impl, .pipe-branch')].some(el => el.scrollWidth > el.clientWidth + 1),
        outside: rects.some(r => r.left < 0 || r.right > innerWidth),
        connected: connectors.length === 6 && connectors.every((r, i) => innerWidth > 1000
          ? Math.abs(r.left - rects[i].right) <= 2 && Math.abs(r.right - rects[i + 1].left) <= 2
          : Math.abs(r.top - rects[i].bottom) <= 2 && Math.abs(r.bottom - rects[i + 1].top) <= 2),
        blocked: document.querySelector('.node.guard .pipe-branch').textContent,
        oldTrack: !!document.querySelector('.pipe-scroll, .wire'),
        grid: [getComputedStyle(document.body, '::before').position, getComputedStyle(document.body, '::before').maskImage],
        glow: getComputedStyle(document.body, '::after').position
      };
    })()`);
    assert.deepEqual(pipeline.groups, ['01 Entry', '02 Processing', '03 Routing']);
    assert.deepEqual(pipeline.names, ['Client', 'Auth', 'Mask', 'Guard', 'Enrich', 'Balance', 'Provider']);
    assert.equal(width > 1000 ? pipeline.horizontal : pipeline.vertical, true, `pipeline direction at ${width}`);
    assert.equal(pipeline.clipped || pipeline.outside, false, `pipeline overflow at ${width}`);
    assert.equal(pipeline.connected, true, `pipeline connections at ${width}`);
    assert.match(pipeline.blocked, /Blocked.*4xx.*no provider call/);
    assert.equal(pipeline.oldTrack, false);
    assert.deepEqual(pipeline.grid, ['fixed', 'none']);
    assert.equal(pipeline.glow, 'absolute');
    if (width <= 1024) {
      assert.equal(await evaluate(`document.getElementById('burger').click(); document.getElementById('navlinks').classList.contains('open')`), true);
      await command('Input.dispatchKeyEvent', {type: 'keyDown', key: 'Escape', code: 'Escape', windowsVirtualKeyCode: 27});
      assert.equal(await evaluate(`!document.getElementById('navlinks').classList.contains('open') && document.activeElement.id === 'burger'`), true);
    }
    assert.equal(await evaluate(`document.getElementById('tab-req').click(); document.getElementById('pane-req').classList.contains('on') && document.getElementById('tab-req').getAttribute('aria-selected') === 'true'`), true);
    await evaluate(`document.querySelector('.install').focus()`);
    await command('Input.dispatchKeyEvent', {type: 'keyDown', key: 'Enter', code: 'Enter', windowsVirtualKeyCode: 13, text: '\r'});
    await command('Input.dispatchKeyEvent', {type: 'keyUp', key: 'Enter', code: 'Enter', windowsVirtualKeyCode: 13});
    let copied = false;
    for (let attempt = 0; attempt < 50; attempt++) {
      copied = await evaluate(`document.querySelector('.install').classList.contains('ok')`);
      if (copied) break;
      await new Promise(resolve => setTimeout(resolve, 20));
    }
    assert.equal(copied, true, 'keyboard copy command: ' + await evaluate(`JSON.stringify({focused: document.hasFocus(), active: document.activeElement.outerHTML, userActivation: navigator.userActivation.isActive})`));
    if (process.argv.includes('--screenshots') && [1440, 390].includes(width)) {
      await new Promise(resolve => setTimeout(resolve, 1500));
      await evaluate(`document.activeElement.blur(); window.scrollTo(0, 0)`);
      const {data} = await command('Page.captureScreenshot', {format: 'png'});
      fs.writeFileSync(path.join(__dirname, `.landing-${width}.png`), Buffer.from(data, 'base64'));
      await evaluate(`document.querySelector('#pipeline').scrollIntoView({behavior: 'instant'})`);
      const clip = await evaluate(`(() => {
        const r = document.querySelector('#pipeline').getBoundingClientRect();
        return {x: r.left + scrollX, y: r.top + scrollY, width: r.width, height: r.height, scale: 1};
      })()`);
      const shot = await command('Page.captureScreenshot', {format: 'png', clip, captureBeyondViewport: true});
      fs.writeFileSync(path.join(__dirname, `.pipeline-${width}.png`), Buffer.from(shot.data, 'base64'));
    }
    await command('Emulation.setEmulatedMedia', {features: [{name: 'prefers-reduced-motion', value: 'no-preference'}]});
    const motion = await evaluate(`(() => {
      const pulses = [...document.querySelectorAll('.pipe-link i')];
      return pulses.map(el => {
        const animation = el.getAnimations()[0];
        const delay = animation.effect.getTiming().delay;
        animation.pause();
        animation.currentTime = delay + 200;
        const start = new DOMMatrix(getComputedStyle(el).transform);
        animation.currentTime = delay + 600;
        const end = new DOMMatrix(getComputedStyle(el).transform);
        return {name: animation.animationName, delay, dx: end.m41 - start.m41, dy: end.m42 - start.m42};
      });
    })()`);
    assert.equal(motion.length, 6);
    motion.forEach((pulse, index) => {
      assert.equal(pulse.name, width > 1000 ? 'pipe-flow-x' : 'pipe-flow-y');
      assert.ok(Math.abs(pulse.delay - index * 800) < 1e-6, 'staggered pulse delay in milliseconds');
      assert.ok(width > 1000 ? pulse.dx > 0 && pulse.dy === 0 : pulse.dy > 0 && pulse.dx === 0);
    });
    await command('Emulation.setEmulatedMedia', {features: [{name: 'prefers-reduced-motion', value: 'reduce'}]});
    assert.equal(await evaluate(`document.querySelector('.pipe-flow').getAnimations({subtree: true}).length`), 0);
    console.log(`Landing ${width}px: layout, pipeline, motion, links, navigation, tabs and copy OK`);
  }
  await command('Emulation.setEmulatedMedia', {features: []});
  await command('Page.reload');
  await new Promise(resolve => setTimeout(resolve, 200));
  await evaluate(`document.querySelector('#features h2').scrollIntoView({behavior: 'instant'})`);
  let revealed = false;
  for (let attempt = 0; attempt < 50; attempt++) {
    revealed = await evaluate(`getComputedStyle(document.querySelector('#features h2')).opacity === '1'`);
    if (revealed) break;
    await new Promise(resolve => setTimeout(resolve, 20));
  }
  assert.equal(revealed, true, 'section revealed during normal scrolling');
  await command('Emulation.setScriptExecutionDisabled', {value: true});
  await command('Page.reload');
  await new Promise(resolve => setTimeout(resolve, 200));
  assert.equal(await evaluate(`[...document.querySelectorAll('.reveal')].every(el => getComputedStyle(el).opacity === '1')`), true, 'content visible without JavaScript');
  assert.deepEqual(errors, []);
  console.log('Landing: scroll reveal, no JavaScript fallback and reduced motion OK');
}

main().catch(error => { console.error(error); process.exitCode = 1; }).finally(async () => {
  await send('Browser.close').catch(() => {});
  await closed;
  fs.rmSync(temporary, {recursive: true, force: true});
});