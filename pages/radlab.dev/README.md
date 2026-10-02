# radlab.dev

## Wpisy blogowe

Każdy wpis jest samodzielnym katalogiem w wybranej wersji językowej:

```text
pl/blog/posts/<slug>/
├── index.md
└── media/
    ├── ilustracja.png
    └── demonstracja.webm

en/blog/posts/<slug>/
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
Powiązania tłumaczeń są w `data/translations.json`.

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
pozostają w `static/img/`.