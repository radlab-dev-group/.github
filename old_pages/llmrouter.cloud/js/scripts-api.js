const sections = [
  { selector: '#header',       url: 'sections/api/header.html' },
  { selector: '#hero',         url: 'sections/api/hero.html' },
  { selector: '#overview',     url: 'sections/api/overview.html' },
  { selector: '#architecture', url: 'sections/api/architecture.html' },
  { selector: '#request-flow', url: 'sections/api/request-flow.html' },
  { selector: '#plugins',      url: 'sections/api/plugins.html' },
  { selector: '#endpoints',    url: 'sections/api/endpoints.html' },
  { selector: '#configuration', url: 'sections/api/configuration.html' },
  { selector: '#lb-strategies', url: 'sections/api/lb-strategies.html' },
  { selector: '#extending',    url: 'sections/api/extending.html' },
  { selector: '#monitoring',   url: 'sections/api/monitoring.html' },
  { selector: '#footer',       url: 'sections/api/footer.html' },

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
    if (event.target.closest("a") && nav.classList.contains("is-open")) {
      nav.classList.remove("is-open");
      toggle.classList.remove("is-open");
      toggle.setAttribute("aria-expanded", "false");
    }
  });
}

// Initialize scroll indicator and back‑to‑top button
function initScrollFeatures() {
  const progressBar = document.getElementById('scroll-progress');
  const backToTopBtn = document.getElementById('back-to-top');

  if (!progressBar || !backToTopBtn) return;

  const updateScroll = () => {
    const scrollTop = window.scrollY || document.documentElement.scrollTop;
    const docHeight = document.documentElement.scrollHeight - window.innerHeight;
    const scrolled = (scrollTop / docHeight) * 100;
    progressBar.style.height = `${scrolled}%`;

    // Show button after scrolling down 200px
    if (scrollTop > 200) {
      backToTopBtn.classList.add('show');
    } else {
      backToTopBtn.classList.remove('show');
    }
  };

  // Smooth scroll to top when button is clicked
  backToTopBtn.addEventListener('click', (e) => {
    e.preventDefault();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });

  window.addEventListener('scroll', updateScroll);
  // Initialise on load
  updateScroll();
}

// Run after all sections are loaded
Promise.all(sections.map(s => loadSection(s.selector, s.url)))
  .catch(err => {
    console.error('Error while loading section:', err);
  })
  .finally(() => {
    initMenuToggle();
    initScrollFeatures();
  });