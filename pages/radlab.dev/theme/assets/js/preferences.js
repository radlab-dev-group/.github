/* Applied before first paint; explicit choices take precedence over the OS. */
(function () {
  'use strict';

  var root = document.documentElement;
  root.classList.add('js');

  function read(key) {
    try { return localStorage.getItem(key); } catch (error) { return null; }
  }

  function save(key, value) {
    try { localStorage.setItem(key, value); } catch (error) { /* private mode */ }
  }

  var media = window.matchMedia('(prefers-color-scheme: dark)');
  var choice = read('radlab-theme');
  if (choice !== 'dark' && choice !== 'light') choice = null;

  function apply(theme) {
    root.setAttribute('data-theme', theme);
    var buttons = document.querySelectorAll('.theme-toggle');
    for (var i = 0; i < buttons.length; i++) {
      buttons[i].setAttribute('aria-pressed', theme === 'dark' ? 'true' : 'false');
    }
  }

  apply(choice || (media.matches ? 'dark' : 'light'));
  document.addEventListener('DOMContentLoaded', function () {
    apply(root.getAttribute('data-theme'));
  });
  var onChange = function (event) {
    if (!choice) apply(event.matches ? 'dark' : 'light');
  };
  if (media.addEventListener) media.addEventListener('change', onChange);
  else if (media.addListener) media.addListener(onChange);

  document.addEventListener('click', function (event) {
    if (!event.target.closest) return;
    var link = event.target.closest('.lang-switch');
    if (link) save('radlab-language', link.getAttribute('lang'));
    if (!event.target.closest('.theme-toggle')) return;
    choice = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    apply(choice);
    save('radlab-theme', choice);
  });

  // Do not replace deep links: readers and crawlers keep the requested article.
  if (root.getAttribute('data-language-auto') !== 'true') return;
  var language = read('radlab-language');
  if (!language || !root.getAttribute('data-language-' + language)) {
    language = root.getAttribute('data-default-lang');
    var languages = navigator.languages || [navigator.language || ''];
    for (var i = 0; i < languages.length; i++) {
      var code = languages[i].toLowerCase().split('-')[0];
      if (root.getAttribute('data-language-' + code)) {
        language = code;
        break;
      }
    }
  }
  var target = root.getAttribute('data-language-' + language);
  if (target && language !== root.getAttribute('lang') && target !== window.location.pathname) {
    window.location.replace(target + window.location.search + window.location.hash);
  }
})();