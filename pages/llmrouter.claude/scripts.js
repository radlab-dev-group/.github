// include.js – ES‑module
// ------------------------------------------------
// Lista sekcji:  selector → plik w katalogu `sections/`
// ------------------------------------------------
const sections = [
  { selector: '#header',       url: 'sections/header.html' },
  { selector: '#why',          url: 'sections/why.html' },
  { selector: '#security',     url: 'sections/security.html' },
  { selector: '#optimization', url: 'sections/optimization.html' },
  { selector: '#use-cases',    url: 'sections/use-cases.html' },
  { selector: '#tech-specs',   url: 'sections/tech-specs.html' },
  { selector: '#cta',          url: 'sections/cta.html' },
  { selector: '#components',   url: 'sections/components.html'},
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
  .catch(err => console.error('Nieoczekiwany błąd przy ładowaniu sekcji:', err));