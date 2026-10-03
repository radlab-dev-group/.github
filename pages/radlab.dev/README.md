# radlab.dev

## Struktura projektu

```text
content/                  # treści i lokalne media
├── pl/                   # home/, products/, pages/, blog/posts/, ui.yaml
└── en/                   # analogicznie
theme/
├── templates/            # szablony HTML i XML
└── assets/               # css/, js/, fonts/, img/
config/
├── site.toml             # ustawienia serwisu
└── translations.json     # powiązania tłumaczeń
tests/
dist/                     # wynik budowania — bez ręcznej edycji
build.py
requirements.txt
```

## Wpisy blogowe

Każdy wpis jest samodzielnym katalogiem w wybranej wersji językowej:

```text
content/pl/blog/posts/<slug>/
├── index.md
└── media/
    ├── ilustracja.png
    └── demonstracja.webm

content/en/blog/posts/<slug>/
├── index.md
└── media/
```

W `index.md` używaj ścieżek względnych do własnego katalogu `media`:

```markdown
---
title: Tytuł wpisu
date: 2025-10-13
slug: przykladowy-wpis
image: media/ilustracja.png
---

![Opis ilustracji](media/ilustracja.png)

{{< video media/demonstracja.webm >}}
```

Obrazy, filmy i inne załączniki zapisuj w repozytorium przy wpisie; builder
nie pobiera ich z sieci ani nie korzysta z mapowania mediów. Wersje PL i EN
mają własne pliki, więc każdy katalog można edytować i przenosić niezależnie.
Osadzenia YouTube pozostają zewnętrzne.

Adresy artykułów nadal wynikają z daty i `slug`, a nie ze struktury źródeł:
`/2025-10-13/przykladowy-wpis/` lub `/en/2025-10-13/przykladowy-wpis/`.
Powiązania tłumaczeń są w `config/translations.json`.

## Panel administracyjny

`admin.py` to prosty system do zarządzania wpisami — okienko Tk, w którym
dodajesz, edytujesz i usuwasz wpisy PL/EN oraz tłumaczysz je na drugi język
przez LLM Router (klient `llm_router_lib`). Lista grupuje wersje tego samego
wpisu w pary (wiersz-nagłówek z podsumowaniem `PL ✓ · EN draft`); pod polami
wpisu klikalna linijka „Wersja EN: …", przycisk „Wersja ↔" i podwójny klik na
wierszu przełączają edytor na drugą wersję, a gdy tłumaczenia brak — od razu
otwierają okno tłumaczenia.

```bash
# interpreter musi mieć rozszerzenie Tk (np. /usr/bin/python3)
/usr/bin/python3 admin.py
LLM_ROUTER_API=http://127.0.0.1:8080 LLM_ROUTER_TOKEN=... /usr/bin/python3 admin.py
```

Logika panelu jest w `admin_core.py` (bez tkintera), testy w
`tests/test_admin_core.py`. Zapisywany jest dokładnie ten sam układ plików,
który czyta `build.py`: katalog `content/<lang>/blog/posts/<slug>/` z
`index.md` (front matter w stylu pozostałych wpisów) i `media/`, a powiązania
tłumaczeń trafiają do `config/translations.json` (`verified: false` do czasu
weryfikacji).

Tłumaczenie działa w obie strony:

- EN → PL: metoda `LLMRouterClient.translate` (endpoint `/api/translate`);
- PL → EN: `extended_conversation_with_model` z systemowym promptem
  „translate to English", bo wbudowany endpoint routera tłumaczy wyłącznie
  na polski.

Tłumaczenie tworzy wersję roboczą (`draft: true`) z przetłumaczonym tytułem,
opisem, tagami, kategoriami i treścią oraz skopiowanymi plikami `media/`
(ścieżki względne w Markdown zostają bez zmian). Slug wersji docelowej
wynika z przetłumaczonego tytułu (kolejny wolny, np. `-2`, przy kolizji).
Model wybiera się w oknie tłumaczenia (lista z routera albo nazwa ręcznie);
tłumaczenie odbywa się w tle, z pulsującym paskiem postępu i statusem
bieżącego pola w pasku statusu.

W edytorze treści dostępne są:

- **Wstaw obraz… / Wstaw film…** — wybiera plik z dysku, kopiuje go do
  `media/` wpisu (przy kolizji nazwy dostaje `-2`, `-3`…) i wstawia w kursorze
  odpowiedni fragment: `![alt](media/plik.png)` albo shortcode
  `{{< video media/plik.webm >}}` (te same osadzenia, co w pozostałych
  wpisach). Jeśli pole „Obraz (media/…)" jest puste, pierwsza wstawiona
  grafika uzupełnia je.
- zakładka **Podgląd** — uproszczony podgląd Markdown (nagłówki, listy,
  cytaty, kod, pogrubienie/kursywa; obrazy i filmy jako placeholdery),
  linki otwierają się po kliknięciu.
- **Buduj stronę…** — wywołuje `python build.py` (opcjonalnie `--fast`,
  `--drafts`, `--check`, `--clean`) w tle; logi budowania trafiają na żywo do
  okna z logami (przycisk „Kopiuj log"), a pasek postępu śledzi etapy
  `[1/5]…[5/5]` raportowane przez build.py. Interpreter z zależnościami
  (markdown, jinja2, pygments, PIL) jest wybierany automatycznie — można go
  nadpisać przez zmienną `BUILDER_PYTHON`.

## Osobne strony

Polityka prywatności jest w `content/{pl,en}/pages/privacy.md` i publikuje się
pod `/privacy/` oraz `/en/privacy/`. Baner zgód i stopka prowadzą do lokalnej
wersji. Pliki `pages/*.md` mają front matter `title`, `description`, opcjonalne
`slug` (domyślnie nazwa pliku) i `updated`; builder dodaje je do sitemap.
Ten sam `slug` w obu językach łączy wersje przez hreflang i przełącznik języka.

## Budowanie

Po instalacji zależności z `requirements.txt` w interpreterze projektu:

```bash
python build.py --check
python build.py --fast --check
python build.py --serve
```

Wynik trafia do `dist/`. Standardowy build generuje i ponownie wykorzystuje
warianty WebP; `--fast` kopiuje lokalne oryginały bez konwersji. Filmy i
załączniki są kopiowane lokalnie w obu trybach. `--check` zgłasza brakujące
media oraz uszkodzone odnośniki. Grafiki wspólne dla całego serwisu, np. logo,
znajdują się w `theme/assets/img/`. Szablony są w `theme/templates/`,
a domyślna konfiguracja w `config/site.toml` (`--config` pozwala wskazać inną).
Układ źródeł nie zmienia publicznych adresów stron i zasobów: wspólne zasoby
są publikowane pod `/assets/`, a oryginalne media wpisów pod
`/<lang>/blog/posts/<slug>/media/` — bez prefiksu `content/`.

## SEO, analityka i preferencje

W `config/site.toml` pole `site.ga_code` włącza Google Analytics na wszystkich
stronach HTML, również na stronie 404. Pusta wartość wyłącza integrację.
Panel zgód PL/EN blokuje skrypt Google i pomiary do momentu akceptacji (basic
consent mode, bez pingów przed zgodą). Akceptacja i odmowa są zapamiętywane
w `localStorage` pod kluczem `radlab-analytics-consent` przez 180 dni.
„Ustawienia prywatności” w stopce pozwalają zmienić decyzję. Wycofanie zgody
wyłącza pomiary, usuwa dostępne cookies GA i przeładowuje stronę, aby zatrzymać
uruchomiony skrypt; nie usuwa danych już wysłanych. Zmiany są synchronizowane
między kartami. Bez JavaScript lub przy odmowie analityka nie jest ładowana.
Przy blokadzie zapisu zgoda dotyczy tylko bieżącej strony. Reklamowe sygnały
Google pozostają wyłączone. Przed publikacją zweryfikuj informacje o administratorze
i przetwarzaniu danych w `content/{pl,en}/pages/privacy.md` oraz `ui.yaml`.
Uzupełnij pełną tożsamość administratora, faktyczne ustawienie retencji w panelu GA4
oraz dostawców hostingu i poczty wraz z okresami przechowywania danych; te informacje
nie wynikają z kodu strony. Ważność decyzji przez 180 dni nie jest retencją danych GA4.

Sekcje `seo.pl` i `seo.en` zawierają tytuły, opisy, hasła tematyczne oraz opisy
bloga. Produkty i artykuły zachowują własne tytuły/opisy, a ich tagi uzupełniają
hasła. Builder dodaje metadane i dane strukturalne Schema.org; 404 ma `noindex`.
Google nie wykorzystuje `meta keywords` do rankingu — istotne pozostają treści,
tytuły, opisy, poprawne adresy kanoniczne, hreflang i sitemap.

Na stronach głównych język wybierany jest według kolejności `navigator.languages`
(PL/EN, domyślnie PL). Bezpośrednie adresy produktów i artykułów nie przekierowują.
Ręczny wybór języka i motywu jest zapamiętywany w `localStorage` i ma pierwszeństwo.
Bez ręcznego wyboru motyw reaguje również na zmianę ustawień systemu w trakcie wizyty.
Usunięcie kluczy `radlab-language` i `radlab-theme` przywraca automatyczny wybór.