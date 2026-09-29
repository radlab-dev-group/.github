/* Progressive enhancements only. Everything here decorates: the theme, the
 * header and the landing page are already correct in HTML and CSS, so a blocked
 * or absent script costs a little motion and nothing else. The inline snippet in
 * <head> applies the stored theme and the `.js` flag before first paint; the
 * `.js` flag is what lets CSS hide-then-reveal without a flash. */
(function () {
  'use strict';

  var KEY = 'radlab-theme';
  var root = document.documentElement;
  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ------------------------------------------------------------------ theme */

  function preferred() {
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }

  function apply(theme) {
    root.setAttribute('data-theme', theme);
    var buttons = document.querySelectorAll('.theme-toggle');
    for (var i = 0; i < buttons.length; i++) {
      buttons[i].setAttribute('aria-pressed', theme === 'dark' ? 'true' : 'false');
    }
  }

  // Reflect the effective theme so aria-pressed is truthful on load.
  apply(root.getAttribute('data-theme') || preferred());

  document.addEventListener('click', function (event) {
    var button = event.target.closest ? event.target.closest('.theme-toggle') : null;
    if (!button) return;
    var next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    apply(next);
    try { localStorage.setItem(KEY, next); } catch (error) { /* private mode */ }
  });

  // Follow the OS while the user has not made an explicit choice.
  var media = window.matchMedia('(prefers-color-scheme: dark)');
  var onChange = function (event) {
    var stored = null;
    try { stored = localStorage.getItem(KEY); } catch (error) { stored = null; }
    if (!stored) apply(event.matches ? 'dark' : 'light');
  };
  if (media.addEventListener) media.addEventListener('change', onChange);
  else if (media.addListener) media.addListener(onChange);

  /* -------------------------------------------------- header state and rule */

  var header = document.querySelector('.site-header');
  var progress = document.querySelector('.scroll-progress span');
  var queued = false;

  function paintHeader() {
    queued = false;
    if (!header) return;
    var y = window.pageYOffset || root.scrollTop || 0;
    header.classList.toggle('is-stuck', y > 8);
    if (progress) {
      var rest = Math.max(root.scrollHeight - window.innerHeight, 1);
      progress.style.width = Math.min(100, (y / rest) * 100) + '%';
    }
  }

  function onScroll() {
    // One write per frame: the handler runs at scroll speed, the paint does not.
    if (queued) return;
    queued = true;
    window.requestAnimationFrame(paintHeader);
  }

  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', onScroll, { passive: true });
  paintHeader();

  /* -------------------------------------------------- reveal on the way down */

  // The elements that gain .reveal are the ones worth easing in; a page that
  // faded every node would read as slow rather than as designed.
  var SELECTOR = '.section-head, .grid > .cell, .contact-card, .feature, .post-list--compact > li';
  var targets = Array.prototype.slice.call(document.querySelectorAll(SELECTOR));
  var stats = Array.prototype.slice.call(document.querySelectorAll('.stat-num[data-count]'));

  if (reduced || !('IntersectionObserver' in window)) {
    // Nothing to hide, nothing to count: the page is already complete.
    return;
  }

  targets.forEach(function (element) { element.classList.add('reveal'); });

  var seen = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (!entry.isIntersecting) return;
      entry.target.classList.add('is-in');
      seen.unobserve(entry.target);
    });
  }, { rootMargin: '0px 0px -8% 0px', threshold: 0.05 });

  targets.forEach(function (element) { seen.observe(element); });

  /* ------------------------------------------------------------ count-up */

  // The written value stays in the DOM, so a reader without this script reads
  // "20+" and never a zero. Only the digits animate; the suffix never moves.
  function countUp(element) {
    var written = element.getAttribute('data-count') || element.textContent;
    var match = written.trim().match(/^(\d+)(.*)$/);
    if (!match) return;
    var target = parseInt(match[1], 10);
    var suffix = match[2];
    var start = null;
    var duration = 950;

    function step(now) {
      if (start === null) start = now;
      var t = Math.min((now - start) / duration, 1);
      var eased = 1 - Math.pow(1 - t, 3);
      element.textContent = Math.round(target * eased) + suffix;
      if (t < 1) window.requestAnimationFrame(step);
      else element.textContent = written.trim();
    }

    element.textContent = '0' + suffix;
    window.requestAnimationFrame(step);
  }

  var counted = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (!entry.isIntersecting) return;
      countUp(entry.target);
      counted.unobserve(entry.target);
    });
  }, { threshold: 0.4 });

  stats.forEach(function (element) { counted.observe(element); });
})();
