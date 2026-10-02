# radlab.dev

## Struktura projektu

```text
content/                  # treści i lokalne media
├── pl/                   # home/, products/, blog/posts/, ui.yaml
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