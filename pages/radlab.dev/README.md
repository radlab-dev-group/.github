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