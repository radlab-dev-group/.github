import { i18n } from './i18n.js';

const sections = [
  { selector: '#header',         url: 'sections/main/header.html' },
  { selector: '#hero',           url: 'sections/main/hero.html' },
  { selector: '#flow-animation', url: 'sections/main/flow_animation.html' },
  { selector: '#quickstart',     url: 'sections/main/quickstart.html' },
  { selector: '#features',       url: 'sections/main/features.html' },
  { selector: '#security',       url: 'sections/main/security.html' },
  { selector: '#performance',    url: 'sections/main/performance.html' },
  { selector: '#ecosystem',      url: 'sections/main/ecosystem.html' },
  { selector: '#monitoring',     url: 'sections/main/monitoring.html' },
  { selector: '#use-cases',      url: 'sections/main/use-cases.html' },
  { selector: '#roadmap',        url: 'sections/main/roadmap.html' },
  { selector: '#open-source',    url: 'sections/main/open-source.html' },
  { selector: '#footer',         url: 'sections/main/footer.html' },
];

async function loadSection(selector, url) {
  const container = document.querySelector(selector);
  if (!container) {
    console.warn(`Cannot find ${selector} – skipping ${url}`);
    return;
  }

  try {
    const response = await fetch(url, { cache: 'no-store' });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const html = await response.text();
    container.innerHTML = html;
  } catch (err) {
    console.error(`Cannot read section ${url}:`, err);
    container.innerHTML = `<p style="color:#c00;">Error during section reading.</p>`;
  }
}

function initMenuToggle() {
  const toggle = document.querySelector(".menu-toggle");
  const nav = document.querySelector(".main-nav");
  if (!toggle || !nav) {
    console.warn("Cannot find .menu-toggle/.main-nav – skipping menu init.");
    return;
  }

  toggle.addEventListener("click", () => {
    const isOpen = nav.classList.toggle("is-open");
    toggle.classList.toggle("is-open", isOpen);
    toggle.setAttribute("aria-expanded", String(isOpen));
  });

  nav.addEventListener("click", (event) => {
    const dropdownTrigger = event.target.closest(".dropdown-trigger");
    if (dropdownTrigger) {
      const dropdown = dropdownTrigger.closest(".nav-dropdown");
      dropdown.classList.toggle("is-open");
      return;
    }

    if (event.target.closest("a") && nav.classList.contains("is-open")) {
      nav.classList.remove("is-open");
      toggle.classList.remove("is-open");
      toggle.setAttribute("aria-expanded", "false");
    }
  });
}

function initLanguageToggle() {
  const langToggle = document.getElementById('lang-toggle');
  if (!langToggle) {
    console.warn("Cannot find #lang-toggle – skipping language toggle init.");
    return;
  }

  const updateToggleButton = () => {
    const currentLang = i18n.getLanguage();
    const langCode = langToggle.querySelector('.lang-code');
    if (langCode) {
      langCode.textContent = currentLang.toUpperCase();
    }
  };

  langToggle.addEventListener('click', () => {
    const currentLang = i18n.getLanguage();
    const newLang = currentLang === 'pl' ? 'en' : 'pl';
    i18n.setLanguage(newLang);
    updateToggleButton();
  });

  window.addEventListener('languageChanged', updateToggleButton);
  updateToggleButton();
}

function initScrollFeatures() {
  const progressBar = document.getElementById('scroll-progress');
  const backToTopBtn = document.getElementById('back-to-top');

  if (!progressBar || !backToTopBtn) return;

  const updateScroll = () => {
    const scrollTop = window.scrollY || document.documentElement.scrollTop;
    const docHeight = document.documentElement.scrollHeight - window.innerHeight;
    const scrolled = (scrollTop / docHeight) * 100;
    progressBar.style.height = `${scrolled}%`;

    if (scrollTop > 200) {
      backToTopBtn.classList.add('show');
    } else {
      backToTopBtn.classList.remove('show');
    }
  };

  backToTopBtn.addEventListener('click', (e) => {
    e.preventDefault();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });

  window.addEventListener('scroll', updateScroll);
  updateScroll();
}

Promise.all(sections.map(s => loadSection(s.selector, s.url)))
  .catch(err => {
    console.error('Error while loading section:', err);
  })
  .finally(() => {
    i18n.init();
    initMenuToggle();
    initLanguageToggle();
    initScrollFeatures();
    setTimeout(initRouterAnimation, 100);
  });
