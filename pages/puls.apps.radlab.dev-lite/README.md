# Puls Informacji by RadLab — lekki frontend webowy (Flask)

Nowoczesny, lekki interfejs webowy implementujący funkcję **Kreatora Aktualności (News Creator)** z ekosystemu RadLab z edytorskim motywem, czytelną typografią artykułów i responsywnym układem.

Zbudowany w oparciu o **Python + Flask + Jinja2 + Vanilla JS + CSS**. Brak ciężkich zależności npm, brak kompilacji TypeScript czy node_modules — całość działa bezpośrednio i natychmiastowo.

## Funkcjonalności

1. **Wczytanie serwisów:** Na starcie pobiera indeksowane kategorie i serwisy (`GET api/public/news_categories_with_pages`).
2. **Zapytanie & Losowanie tematów:** Użytkownik wpisuje zapytanie lub wybiera jedną z losowych podpowiedzi z pliku `kreator-pytania.txt` (losowane po 3 propozycje z opcją przelosowania).
3. **Konfiguracja:** Wybór stylu (**zrozumiała dla każdego / formalny język**) oraz zakresu czasu (**Dziś / 2 dni / Tydzień**).
4. **Wyszukiwanie:** `POST api/public/search_news` (form-encoded) z wyliczaniem optymalnej liczby wyników i filtrem serwisów.
5. **Wykres polaryzacji:** Wykres rozkładu polaryzacji 3c (pozytywny, negatywny, ambiwalentny) w czystym CSS.
6. **Generowanie artykułu:** `POST api/public/generate_article_from_search` przez model RAG.
7. **Prezentacja artykułu:** Sformatowany arkusz czytelniczy z drop-cap, szacowanym czasem czytania, liczbą słów, kopiowaniem do schowka, pobieraniem `.md` oraz szczegółami technicznymi.
8. **Materiał źródłowy:** Przegląd dopasowanych wiadomości w trybie kart poziomych (wire) lub listy, z odnośnikami do oryginalnych serwisów.

## Architektura

```
przeglądarka
  └─ /api/search, /api/generate  (Flask app.py proxy)
        └─ RADLAB_API_HOST       (radlab backend, form-encoded)
```

Lekki serwer Flask (`app.py`) przekazuje wywołania do backendu RadLab, omijając ograniczenia CORS w przeglądarce i zachowując spójność z aplikacją `radar.apps.radlab.dev`.

## Uruchomienie

### 1. Zależności

```bash
pip install -r requirements.txt
```

### 2. Uruchomienie serwera

```bash
./run.sh
```

lub bezpośrednio przez Python / Gunicorn:

```bash
PORT=5101 python3 app.py
# lub
gunicorn -w 2 -b 0.0.0.0:5101 app:app
```

Aplikacja będzie dostępna pod adresem: `http://localhost:5101` (lub wskazanym w zmiennej `$PORT`).

## Konfiguracja (`config/config.json` lub zmienne środowiskowe)

| Zmienna środowiskowa | Domyślna wartość w config.json |
|---|---|
| `RADLAB_API_HOST` | `http://192.168.100.79:8567` |
| `RADLAB_EP_NEWS_CATEGORIES` | `api/public/news_categories_with_pages` |
| `RADLAB_EP_SEARCH_NEWS` | `api/public/search_news` |
| `RADLAB_EP_GENERATE_ARTICLE` | `api/public/generate_article_from_search` |
| `RADLAB_PREDEFINED_QUERIES_PATH` | `kreator-pytania.txt` |
| `PORT` | `5101` |
