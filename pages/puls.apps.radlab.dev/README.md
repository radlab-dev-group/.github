# Puls Informacji by RadLab — News Creator (Flask Edition)

Wersja aplikacji **Puls Informacji** przepisana z Next.js/React na **Python Flask + szablony Jinja2**.

Aplikacja stanowi lekki, bezpieczny i wydajny interfejs dla **Kreatora Aktualności (News Creator)** opartego o RAG i indeks wiadomości RadLab.

## Architektura i Bezpieczeństwo

* **Python Flask + szablony Jinja2**: Uruchomienie aplikacji nie wymaga Node.js ani `node_modules`.
* **Czyste szablony + statyczny CSS/JS**: Gotowy arkusz CSS jest dostarczany lokalnie. Nie ma etapu kompilacji ani narzędzi npm; przeglądarka nie pobiera frameworka z CDN.
* **Wbudowane zabezpieczenia**:
  * Ochrona przed XSS poprzez automatyczne escapowanie Jinja2 oraz bezpieczny parser Markdown w Pythonie (`markdown_utils.py`).
  * Nagłówki bezpieczeństwa HTTP (`X-Content-Type-Options: nosniff`, `X-Frame-Options: SAMEORIGIN`, `Referrer-Policy: strict-origin-when-cross-origin`).
  * Bezpieczne proxy do wewnętrznego API radlab.

## Struktura katalogu

```
flask_app/
├── app.py                      # Główny plik aplikacji Flask i endpointy proxy
├── i18n.py                     # Słownik wielojęzyczny (PL / EN)
├── markdown_utils.py           # Bezpieczny parser Markdown i formatowanie artykułu
├── kreator-pytania.txt         # Baza predefiniowanych pytań dla użytkownika
├── requirements.txt            # Zależności Python (flask, requests, gunicorn, python-dotenv)
├── run.sh                      # Skrypt uruchomieniowy (produkcja/dev)
├── config/
│   └── config.json             # Domyślna konfiguracja hosta i endpointów
├── static/
│   ├── css/
│   │   └── style.css           # Style interfejsu i typografia artykułu
│   ├── js/
│   │   └── app.js              # Klient JavaScript dla dynamicznego interfejsu
│   └── img/
│       ├── logo-circle.png     # Logo RadLab
│       └── logo.png
└── templates/
    ├── base.html               # Szablon bazowy z nagłówkiem i stopką
    └── index.html              # Główny szablon kreatora artykułów
```

## Uruchomienie

### 1. Za pomocą skryptu `run.sh`:

```bash
cd pages/puls.apps.radlab.dev/flask_app
./run.sh
```

Domyślnie aplikacja uruchamia się na porcie `5200`: `http://localhost:5200`

### 2. Tryb developerski:

```bash
FLASK_DEBUG=1 PORT=5200 ./run.sh
```

lub bezpośrednio:

```bash
python3 -m pip install -r requirements.txt
python3 app.py
```

## Aktualizacja stylów

Style edytuj bezpośrednio w `static/css/style.css` (nowe reguły można dopisywać na końcu pliku).
Arkusz zachowuje dotychczasowy wygląd i nie wymaga przebudowy.
Po dodaniu nowych klas w szablonach, JavaScript lub parserze Markdown dodaj ich reguły do CSS,
jeżeli nie ma ich jeszcze w arkuszu. Pliki w `static/` są częścią aplikacji i należy je zachować.

## Konfiguracja (`.env` / `config/config.json`)

| Zmienna | Domyślna wartość | Opis |
|---|---|---|
| `RADLAB_API_HOST` | `http://192.168.100.79:8567` | Adres hosta API backendu RadLab |
| `RADLAB_EP_NEWS_CATEGORIES` | `api/public/news_categories_with_pages` | Endpoint kategorii i stron |
| `RADLAB_EP_SEARCH_NEWS` | `api/public/search_news` | Endpoint wyszukiwania newsów |
| `RADLAB_EP_GENERATE_ARTICLE` | `api/public/generate_article_from_search` | Endpoint generowania artykułu |
| `RADLAB_PREDEFINED_QUERIES_PATH` | `kreator-pytania.txt` | Ścieżka do pliku z pytaniami |
| `PORT` | `5200` | Port aplikacji webowej |
| `FLASK_DEBUG` | `0` | Tryb debugowania (1 - dev, 0 - prod) |
