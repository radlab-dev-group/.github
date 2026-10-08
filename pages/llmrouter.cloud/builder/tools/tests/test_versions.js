const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const source = fs.readFileSync(path.join(__dirname, '../theme/docs.js'), 'utf8');
const versionsCode = source.slice(source.indexOf('  function initVersions()'),
  source.indexOf('  /* ---- code blocks:'));

function element(attrs) {
  return {
    attrs,
    getAttribute(name) { return this.attrs[name] ?? null; },
    setAttribute(name, value) { this.attrs[name] = value; },
    addEventListener(name, fn) { this[name] = fn; },
  };
}

function select(repo, versions, selected, base) {
  const el = element({'data-switch': repo});
  el.options = versions.map(version => element({
    'data-version': version,
    'data-root': new URL(`${repo === 'router' ? '' : repo + '/'}${version === 'latest' ? '' : version + '/'}index.html`, base).href,
  }));
  el.options.forEach(option => { option.value = option.getAttribute('data-root'); });
  el.selectedIndex = versions.indexOf(selected);
  Object.defineProperty(el, 'value', {
    get() { return this.options[this.selectedIndex].value; },
    set(value) { this.selectedIndex = this.options.findIndex(option => option.value === value); },
  });
  return el;
}

async function fixture(url, active, routerVersion, pluginVersion, serviceVersion = '0.5.0', opened = []) {
  const base = 'https://example.invalid/sub/docs/';
  const router = select('router', ['1.1.0', '1.0.0'], routerVersion, base);
  const plugins = select('plugins', ['0.2.0', '0.1.0'], pluginVersion, base);
  const services = select('services', ['0.5.0', '0.4.0'], serviceVersion, base);
  const handlers = {};
  const groups = {};
  const requests = [];
  const doc = {
    addEventListener(name, fn) { handlers[name] = fn; },
    querySelector(selector) { return groups[selector] || null; },
  };
  const selectors = [router, plugins, services];
  const window = {location: {href: url}};
  const body = element({'data-repo': active, 'data-docs-root': base});
  class DOMParser {
    parseFromString() {
      return {querySelector(selector) {
        const link = element({href: 'overview.html', class: 'active'});
        link.classList = {remove() { link.attrs.class = ''; }};
        const details = {open: true};
        const group = {querySelector() { return details; }, querySelectorAll(selector) {
          if (selector === 'a[href]') return [link];
          if (selector === '.active') return [link];
          return [];
        }};
        group.link = link;
        group.details = details;
        group.routerContext = selector === '[data-nav-repo="router"]';
        return group;
      }};
    }
  }
  for (const repo of ['router', 'plugins', 'services']) {
    groups[`[data-nav-repo="${repo}"]`] = {querySelector() { return {open: opened.includes(repo)}; }, replaceWith(group) {
      groups[repo] = group;
    }};
    groups[`[data-versions-repo="${repo}"]`] = {open: true, replaceWith(group) {
      groups[`${repo}Versions`] = group;
    }};
  }
  groups['[data-router-context]'] = {replaceWith(group) {
    groups.routerContext = group;
  }};
  groups['[data-router-release]'] = {replaceWith(group) {
    groups.routerRelease = group;
  }};
  const context = vm.createContext({
    doc, body, window, URL, DOMParser,
    all(selector, root) {
      return root ? Array.from(root.querySelectorAll(selector)) : selectors;
    },
    fetch(target) {
      requests.push(target);
      return Promise.resolve({ok: true, text: () => Promise.resolve('sidebar')});
    },
  });
  vm.runInContext(versionsCode + '\ninitVersions();', context);
  await new Promise(resolve => setImmediate(resolve));
  function change(el, version) {
    el.selectedIndex = el.options.findIndex(o => o.getAttribute('data-version') === version);
    if (handlers.change) handlers.change({target: el});
    else el.change();
    return new URL(window.location.href);
  }
  return {router, plugins, services, groups, requests, handlers, change};
}

(async () => {
  const first = await fixture('https://example.invalid/sub/docs/1.0.0/index.html', 'router', '1.0.0', '0.2.0');
  const target = first.change(first.plugins, '0.1.0');
  assert.equal(target.pathname, '/sub/docs/plugins/0.1.0/index.html');
  assert.equal(target.searchParams.get('router'), '1.0.0', 'plugin switch must retain the router release');
  assert.equal(target.searchParams.get('plugins'), '0.1.0');

  const second = await fixture(target.href, 'plugins', '1.1.0', '0.1.0');
  assert.equal(second.router.options[second.router.selectedIndex].getAttribute('data-version'), '1.0.0');
  assert.deepEqual(second.requests, ['https://example.invalid/sub/docs/1.0.0/index.html']);
  assert.equal(second.groups.router.link.getAttribute('href'), 'https://example.invalid/sub/docs/1.0.0/overview.html');
  assert.ok(second.groups.router.routerContext, 'router heading must be restored inside its navigation group');
  assert.equal(second.groups.router.details.open, false, 'restoring a release must retain the collapsed menu');
  assert.equal(second.groups.routerVersions.open, true, 'restoring a release must retain the expanded version list');
  assert.ok(second.groups.routerVersions, 'router versions panel must follow the selected router');
  assert.equal(second.groups.routerVersions.link.getAttribute('href'), 'https://example.invalid/sub/docs/1.0.0/overview.html');
  assert.equal(second.groups.pluginsVersions, undefined, 'router restoration must not replace the plugins panel');
  assert.ok(second.groups.routerRelease, 'router release panel must follow the selected router on plugin hubs');
  assert.equal(second.groups.routerRelease.link.getAttribute('href'), 'https://example.invalid/sub/docs/1.0.0/overview.html');
  const routerTarget = second.change(second.router, '1.1.0');
  assert.equal(routerTarget.searchParams.get('plugins'), '0.1.0', 'router switch must retain plugins');

  const third = await fixture(routerTarget.href, 'router', '1.1.0', '0.2.0');
  assert.deepEqual(third.requests, ['https://example.invalid/sub/docs/plugins/0.1.0/index.html']);
  assert.equal(third.groups.plugins.link.getAttribute('href'), 'https://example.invalid/sub/docs/plugins/0.1.0/overview.html');
  assert.equal(third.groups.routerContext, undefined, 'restoring plugins must not replace the router heading');
  assert.ok(third.groups.pluginsVersions, 'plugins versions panel must follow the selected plugins');
  assert.equal(third.groups.routerRelease, undefined, 'restoring plugins must not replace the router release panel');
  const versionLink = element({href: 'https://example.invalid/sub/docs/plugins/0.2.0/index.html',
    'data-version-repo': 'plugins', 'data-version': '0.2.0'});
  versionLink.closest = () => versionLink;
  third.handlers.click({target: versionLink});
  const versionTarget = new URL(versionLink.getAttribute('href'));
  assert.equal(versionTarget.searchParams.get('router'), '1.1.0');
  assert.equal(versionTarget.searchParams.get('plugins'), '0.2.0', 'version link must override only its own selection');
  const link = element({href: 'https://example.invalid/sub/docs/1.1.0/guide.html#example'});
  link.closest = () => link;
  third.handlers.click({target: link});
  assert.equal(new URL(link.getAttribute('href')).searchParams.get('plugins'), '0.1.0');
  assert.equal(new URL(link.getAttribute('href')).hash, '#example');
  const external = element({href: 'https://github.com/example/docs/index.html'});
  external.closest = () => external;
  third.handlers.click({target: external});
  assert.equal(external.getAttribute('href'), 'https://github.com/example/docs/index.html');
  const anchor = element({href: '#example'});
  anchor.closest = () => anchor;
  third.handlers.click({target: anchor});
  assert.equal(anchor.getAttribute('href'), '#example');
  const newTab = element({href: 'https://example.invalid/sub/docs/plugins/0.1.0/guides/guide.html'});
  newTab.closest = () => newTab;
  third.handlers.auxclick({target: newTab});
  assert.equal(new URL(newTab.getAttribute('href')).searchParams.get('router'), '1.1.0');

  const rolling = await fixture('https://example.invalid/sub/docs/1.0.0/index.html?plugins=rolling', 'router', '1.0.0', '0.2.0');
  assert.equal(rolling.change(rolling.router, '1.1.0').searchParams.get('plugins'), '0.2.0');

  const serviceTarget = third.change(third.services, '0.4.0');
  assert.equal(serviceTarget.pathname, '/sub/docs/services/0.4.0/index.html');
  assert.equal(serviceTarget.searchParams.get('router'), '1.1.0');
  assert.equal(serviceTarget.searchParams.get('plugins'), '0.1.0');
  const servicePage = await fixture(serviceTarget.href, 'services', '1.1.0', '0.2.0', '0.4.0');
  assert.equal(servicePage.change(servicePage.plugins, '0.2.0').searchParams.get('services'), '0.4.0');
  const restored = await fixture('https://example.invalid/sub/docs/1.0.0/index.html?services=0.4.0', 'router', '1.0.0', '0.2.0');
  assert.deepEqual(restored.requests, ['https://example.invalid/sub/docs/services/0.4.0/index.html']);
  assert.ok(restored.groups.servicesVersions, 'services panel must follow the selected services');
  assert.equal(restored.groups.services.link.getAttribute('href'), 'https://example.invalid/sub/docs/services/0.4.0/overview.html');
  assert.equal(restored.groups.routerContext, undefined);
  assert.equal(restored.groups.routerRelease, undefined, 'restoring services must not replace the router release panel');

  const invalid = await fixture('https://example.invalid/sub/docs/plugins/0.1.0/index.html?router=bogus&plugins=0.2.0', 'plugins', '1.1.0', '0.1.0');
  assert.equal(invalid.requests.length, 0);
  assert.equal(invalid.plugins.options[invalid.plugins.selectedIndex].getAttribute('data-version'), '0.1.0');
  for (const repo of ['router', 'plugins', 'services']) {
    const active = repo === 'plugins' ? 'router' : 'plugins';
    const opened = await fixture(`https://example.invalid/sub/docs/${active === 'router' ? '1.1.0' : 'plugins/0.2.0'}/guide.html?router=1.0.0&plugins=0.1.0&services=0.4.0`,
      active, '1.1.0', '0.2.0', '0.5.0', [repo]);
    assert.equal(opened.groups[repo].details.open, true,
      'asynchronous navigation restoration must retain an expanded repository');
  }
  console.log('Independent version navigation: OK');
})().catch(error => { console.error(error); process.exitCode = 1; });