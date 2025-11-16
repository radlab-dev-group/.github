// include.js – ES‑module
// ------------------------------------------------
// Lista sekcji:  selector → plik w katalogu `sections/`
// ------------------------------------------------
const sections = [
  { selector: '#header',       url: 'sections/header.html' },
  { selector: '#hero',         url: 'sections/hero.html' },
  { selector: '#features',     url: 'sections/features.html' },
  { selector: '#security',     url: 'sections/security.html' },
  { selector: '#performance',  url: 'sections/performance.html' },
  { selector: '#use-cases',    url: 'sections/use-cases.html' },
  { selector: '#open-source',  url: 'sections/open-source.html' },
  { selector: '#footer',       url: 'sections/footer.html' },
];

/**
 * Pobiera plik HTML i wstawia go do elementu wskazanego selektorem.
 * @param {string} selector - CSS selector (np. "#header")
 * @param {string} url      - ścieżka do pliku HTML
 */
async function loadSection(selector, url) {
  const container = document.querySelector(selector);
  if (!container) {
    console.warn(`Brak elementu ${selector} – pomijam wczytywanie ${url}`);
    return;
  }

  try {
    const response = await fetch(url, { cache: 'no-store' });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const html = await response.text();
    container.innerHTML = html;
  } catch (err) {
    console.error(`Nie udało się wczytać sekcji ${url}:`, err);
    container.innerHTML = `<p style="color:#c00;">Błąd wczytywania sekcji.</p>`;
  }
}

// Uruchom wszystkie wczytania równocześnie
Promise.all(sections.map(s => loadSection(s.selector, s.url)))
  .catch(err => {
    console.error('Nieoczekiwany błąd przy ładowaniu sekcji:', err);
  })
  .finally(() => {
    initMenuToggle();
  });

function initMenuToggle() {
  const toggle = document.querySelector(".menu-toggle");
  const nav = document.querySelector(".main-nav");
  if (!toggle || !nav) {
    console.warn("Nie znaleziono .menu-toggle lub .main-nav – pomijam inicjalizację menu.");
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