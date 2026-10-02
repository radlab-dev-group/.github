/* Progressive enhancements only. Everything here decorates: the theme, the
 * header and the landing page are already correct in HTML and CSS, so a blocked
 * or absent script costs a little motion and nothing else. preferences.js in
 * <head> applies the stored theme and the `.js` flag before first paint; the
 * `.js` flag is what lets CSS hide-then-reveal without a flash. */
(function () {
  'use strict';

  var root = document.documentElement;
  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

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

  /* ---------------------------------- the mark leans towards the pointer */

  // Only where there is a pointer to follow and room for the orbit: below the
  // breakpoint the stage is a stacked block with the pills under it, and a
  // element that drifts under a fingertip is an annoyance, not a detail.
  var stage = document.querySelector('.hero-stage');
  var hero = stage && stage.closest ? stage.closest('.hero') : null;
  if (stage && hero && !reduced
      && window.matchMedia('(min-width: 1000px)').matches
      && window.matchMedia('(hover: hover) and (pointer: fine)').matches) {

    var mark = stage.querySelector('.orb-orbit');
    var system = stage.querySelector('.orbits');
    // Peak-to-peak travel, read from the stylesheet: the orbit diagram can
    // afford a wide swing where it has room, the parked labels cannot, and the
    // CSS is the only place that knows which of the two is showing.
    var declared = getComputedStyle(stage);
    var REACH = {
      x: parseFloat(declared.getPropertyValue('--reach-x')) || 46,
      y: parseFloat(declared.getPropertyValue('--reach-y')) || 32
    };
    var want = { x: 0, y: 0 };
    var at = { x: 0, y: 0 };
    var frame = null;

    function glide() {
      frame = null;
      // A damped chase rather than a direct set: the lag is what reads as
      // weight, and it settles back to rest instead of snapping.
      at.x += (want.x - at.x) * 0.09;
      at.y += (want.y - at.y) * 0.09;
      if (mark) mark.style.transform = 'translate3d(' + at.x.toFixed(2) + 'px,' + at.y.toFixed(2) + 'px,0)';
      // The labels go where their star goes -- the rings are a system, not a
      // second plane, and the mesh behind them, which does not move, is what
      // gives the scene its depth.
      if (system) system.style.transform = 'translate3d(' + at.x.toFixed(2) + 'px,' + at.y.toFixed(2) + 'px,0)';
      if (Math.abs(want.x - at.x) > 0.1 || Math.abs(want.y - at.y) > 0.1) {
        frame = window.requestAnimationFrame(glide);
      }
    }

    function aim(event) {
      var box = hero.getBoundingClientRect();
      want.x = ((event.clientX - box.left) / box.width - 0.5) * REACH.x;
      want.y = ((event.clientY - box.top) / box.height - 0.5) * REACH.y;
      if (frame === null) frame = window.requestAnimationFrame(glide);
    }

    hero.addEventListener('pointermove', aim);
    hero.addEventListener('pointerleave', function () {
      want.x = 0; want.y = 0;
      if (frame === null) frame = window.requestAnimationFrame(glide);
    });
  }

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

(function () {
  'use strict';
  if (!navigator.clipboard || !navigator.clipboard.writeText || !window.isSecureContext) return;
  var labels = document.body.dataset;
  document.querySelectorAll('.prose pre > code').forEach(function (code) {
    var pre = code.parentNode;
    var wrapper = document.createElement('div');
    wrapper.className = 'code-copy-wrapper';
    pre.parentNode.insertBefore(wrapper, pre);
    wrapper.appendChild(pre);
    var button = document.createElement('button');
    button.type = 'button';
    button.className = 'code-copy';
    button.textContent = labels.copyCode;
    var status = document.createElement('span');
    status.className = 'code-copy-status';
    status.setAttribute('role', 'status');
    wrapper.appendChild(button);
    wrapper.appendChild(status);
    button.addEventListener('click', function () {
      button.disabled = true;
      navigator.clipboard.writeText(code.textContent).then(function () {
        status.textContent = labels.codeCopied;
        button.disabled = false;
      }, function () {
        status.textContent = labels.copyFailed;
        button.disabled = false;
      });
    });
  });
})();
