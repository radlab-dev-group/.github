/* Basic consent mode: no Google requests before explicit analytics consent. */
(function () {
  'use strict';

  var panel = document.getElementById('analytics-consent');
  if (!panel) return;
  var code = panel.getAttribute('data-ga-code');
  if (!code) return;
  var key = 'radlab-analytics-consent';
  var lifetime = 180 * 24 * 60 * 60 * 1000;
  var loaded = false;
  var returnFocus = null;
  var settings = document.querySelector('[data-consent-settings]');

  function readChoice() {
    try {
      var saved = JSON.parse(localStorage.getItem(key));
      if (saved && saved.version === 1 && typeof saved.time === 'number'
          && saved.time <= Date.now() && Date.now() - saved.time < lifetime
          && (saved.choice === 'granted' || saved.choice === 'denied')) return saved.choice;
    } catch (_) { /* Unavailable storage means consent lasts for this page only. */ }
    return null;
  }

  function clearCookies() {
    var domains = [''];
    var host = window.location.hostname.split('.');
    while (host.length > 1) {
      domains.push(host.join('.'));
      host.shift();
    }
    var paths = ['/'];
    var parts = window.location.pathname.split('/').filter(Boolean);
    while (parts.length) {
      paths.push('/' + parts.join('/'), '/' + parts.join('/') + '/');
      parts.pop();
    }
    document.cookie.split(';').forEach(function (cookie) {
      var name = cookie.split('=')[0].trim();
      if (!/^(_ga(?:_|$)|_gid$|_gat(?:_|$))/.test(name)) return;
      domains.forEach(function (domain) {
        paths.forEach(function (path) {
          document.cookie = name + '=; Max-Age=0; path=' + path
            + (domain ? '; domain=' + domain : '') + '; SameSite=Lax';
        });
      });
    });
  }

  function enableAnalytics() {
    if (loaded) return;
    loaded = true;
    window['ga-disable-' + code] = false;
    window.dataLayer = window.dataLayer || [];
    window.gtag = function () { window.dataLayer.push(arguments); };
    window.gtag('consent', 'default', {
      analytics_storage: 'granted', ad_storage: 'denied',
      ad_user_data: 'denied', ad_personalization: 'denied'
    });
    window.gtag('js', new Date());
    window.gtag('config', code, { allow_google_signals: false, allow_ad_personalization_signals: false });
    var script = document.createElement('script');
    script.async = true;
    script.src = 'https://www.googletagmanager.com/gtag/js?id=' + encodeURIComponent(code);
    document.head.appendChild(script);
  }

  function disableAnalytics() {
    window['ga-disable-' + code] = true;
    try { clearCookies(); } catch (_) { /* Cookies can be blocked alongside storage. */ }
    // A reload also removes already-running vendor timers and event listeners.
    if (loaded) window.location.reload();
  }

  function apply(choice) {
    panel.hidden = choice !== null;
    if (choice === 'granted') enableAnalytics();
    else disableAnalytics();
  }

  panel.querySelectorAll('[data-consent-choice]').forEach(function (button) {
    button.addEventListener('click', function () {
      var choice = button.getAttribute('data-consent-choice');
      try {
        localStorage.setItem(key, JSON.stringify({ version: 1, choice: choice, time: Date.now() }));
      } catch (_) { /* Do not prevent a choice when persistence is blocked. */ }
      apply(choice);
      if (returnFocus) returnFocus.focus();
      else if (settings) settings.focus();
    });
  });

  if (settings) {
    settings.hidden = false;
    settings.addEventListener('click', function () {
      returnFocus = settings;
      panel.hidden = false;
      panel.querySelector('[data-consent-choice]').focus();
    });
  }
  window.addEventListener('storage', function (event) {
    if (event.key === key || event.key === null) apply(readChoice());
  });
  apply(readChoice());
})();