const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const test = require('node:test');

const css = fs.readFileSync(path.join(__dirname, '../theme/assets/css/site.css'), 'utf8');

for (const [viewport, column, count] of [[1440, 460, 8], [1440, 460, 10],
  [1100, 376, 8], [1100, 376, 10]]) {
  test(`${count} orbit labels remain separated: viewport ${viewport}`, () => {
    const labels = ['pLLama3-8B', 'bi-encodery', 'RAG', 'LLM Router', 'PII Masker',
      'vLLM / Ollama', 'Guardrails', 'Information Radar', 'NER / ONNX', 'Open source'].slice(0, count);
    const html = `<!doctype html><meta charset="utf-8"><style>${css}
      body { width: ${column}px; margin: 60px; }
      .orb-orbit, .orbits, .orb { animation: none; }
      </style><div class="hero-stage"><span class="orb-orbit"><span class="orb"></span></span>
      <ul class="orbits orbits--extended">${labels.map(label =>
        `<li class="orbit"><span class="orbit-arm"><span class="chip">${label}</span></span></li>`).join('')}</ul></div>
      <script>
      const errors = [];
      if (${viewport} >= 1280) {
        const rings = Array.from(document.querySelectorAll('.orbit'), ring => getComputedStyle(ring));
        if (new Set(rings.map(style => style.getPropertyValue('--r').trim())).size < 3)
          errors.push('orbit radii must vary');
        if (new Set(rings.map(style => style.getPropertyValue('--inc').trim())).size < 3)
          errors.push('orbit inclinations must vary');
        const starRadius = document.querySelector('.orb').getBoundingClientRect().width / 2;
        if (!rings.some(style => parseFloat(style.getPropertyValue('--r')) *
            Math.cos(parseFloat(style.getPropertyValue('--inc')) * Math.PI / 180) < starRadius))
          errors.push('far-side orbits must pass behind the star');
      }
      const animations = document.getAnimations();
      animations.forEach(animation => animation.pause());
      let behindStar = false;
      for (let phase = 0; phase < 72; phase++) {
        animations.forEach(animation => { animation.currentTime = phase * 150000 / 72; });
        const boxes = Array.from(document.querySelectorAll('.chip'), chip => chip.getBoundingClientRect());
        const star = document.querySelector('.orb');
        const starBox = star.getBoundingClientRect();
        boxes.forEach((box, index) => {
          const x = box.left + box.width / 2, y = box.top + box.height / 2;
          const chip = document.querySelectorAll('.chip')[index];
          const arm = new DOMMatrix(getComputedStyle(chip.parentElement).transform);
          const inclination = parseFloat(getComputedStyle(chip).getPropertyValue('--inc'));
          // Chromium hit testing ignores the painted order of these 3D planes.
          // Check the far-side depth, projected position and dimming instead.
          if (Math.hypot(x - starBox.left - starBox.width / 2,
              y - starBox.top - starBox.height / 2) < starBox.width / 2 - 5 &&
              arm.m42 * Math.sin(inclination * Math.PI / 180) < -100 &&
              parseFloat(getComputedStyle(chip).opacity) < 0.5)
            behindStar = true;
          if (!box.width || !box.height || box.left < 0 || box.right > ${viewport})
            errors.push('invalid bounds at phase ' + phase + ': ' + index);
          boxes.slice(index + 1).forEach((other, offset) => {
            if (box.left < other.right && box.right > other.left &&
                box.top < other.bottom && box.bottom > other.top)
              errors.push('overlap at phase ' + phase + ': ' + index + '/' + (index + offset + 1)
                + (phase === 0 ? ' bounds ' + [box.x, box.y, box.width, box.height, other.x, other.y, other.width, other.height].join(',') : ''));
          });
        });
      }
      if (${viewport} >= 1280 && !behindStar) errors.push('labels never disappear behind the star');
      document.body.setAttribute('data-layout-result', errors.length ? errors.join('; ') : 'pass');
      </script>`;
    const result = spawnSync(process.env.CHROMIUM || 'chromium', [
      '--headless', '--no-sandbox', '--disable-gpu', '--dump-dom', `--window-size=${viewport},900`,
      'data:text/html;base64,' + Buffer.from(html).toString('base64'),
    ], { encoding: 'utf8', timeout: 20000, maxBuffer: 2 * 1024 * 1024 });
    assert.equal(result.status, 0, result.error?.message || result.stderr);
    assert.equal(result.stdout.match(/data-layout-result="[^"]*"/)?.[0], 'data-layout-result="pass"');
  });
}

// Run explicitly with: node --test tests/test_hero_layout.js (requires Chromium).
for (const [viewport, column] of [[1440, 460], [1100, 376], [800, 320]]) {
  test(`dense hero labels fit without overlap: viewport ${viewport}, column ${column}`, () => {
    const stages = [11, 12, 24].map(count => {
      const labels = Array.from({ length: count }, (_, index) =>
        `<li class="orbit"><span class="orbit-arm"><span class="chip">${index === 0
          ? 'LongTechnologyName'.repeat(12) : `Information Radar ${index}`}</span></span></li>`).join('');
      return `<div class="hero-stage hero-stage--dense">
        <span class="orb-orbit"><span class="orb"></span></span>
        <ul class="orbits orbits--wrapped">${labels}</ul></div>`;
    }).join('');
    const html = `<!doctype html><meta charset="utf-8"><style>${css}
      body { width: ${column}px; margin: 0; }
      *, *::before, *::after { animation: none !important; }
      </style>${stages}<script>
      const errors = [];
      document.querySelectorAll('.hero-stage').forEach(stage => {
        const bounds = stage.getBoundingClientRect();
        const orb = stage.querySelector('.orb').getBoundingClientRect();
        const labels = Array.from(stage.querySelectorAll('.chip'), chip => chip.getBoundingClientRect());
        labels.forEach((box, index) => {
          if (box.left < bounds.left - 1 || box.right > bounds.right + 1 ||
              box.bottom > bounds.bottom + 1 || box.top < orb.bottom)
            errors.push('label outside stage or over orb: ' + index);
          labels.slice(index + 1).forEach(other => {
            if (box.left < other.right && box.right > other.left &&
                box.top < other.bottom && box.bottom > other.top)
              errors.push('overlapping labels: ' + index);
          });
        });
      });
      document.body.setAttribute('data-layout-result', errors.length ? errors.join('; ') : 'pass');
      </script>`;
    const result = spawnSync(process.env.CHROMIUM || 'chromium', [
      '--headless', '--no-sandbox', '--disable-gpu', '--dump-dom',
      `--window-size=${viewport},900`,
      'data:text/html;base64,' + Buffer.from(html).toString('base64'),
    ], { encoding: 'utf8', timeout: 20000, maxBuffer: 2 * 1024 * 1024 });
    assert.equal(result.status, 0, result.error?.message || result.stderr);
    assert.match(result.stdout, /data-layout-result="pass"/,
      result.stdout.match(/data-layout-result="[^"]*"/)?.[0] || result.stderr);
  });
}