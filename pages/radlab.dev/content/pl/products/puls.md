---
title: "Puls Informacji"
subtitle: "Wiadomości z wielu źródeł zebrane w jeden artykuł na wybrany temat"
slug: "puls"
description: "Puls Informacji to aplikacja internetowa RadLab, która tworzy artykuły w odpowiedzi na pytania o bieżące wydarzenia. Korzysta z własnego indeksu wiadomości z wielu serwisów, dołącza linki do źródeł i przedstawia analizę wydźwięku wyszukanych tekstów."
icon: "spark"
status: "Aplikacja internetowa · Wersja demonstracyjna"
version: "Next.js 15 · RAG"
tags: ["RAG", "Generative AI", "Information Synthesis", "News Search", "Polarity 3C", "Local Index"]
actions:
  - {label: "Otwórz aplikację (puls.apps.radlab.dev)", href: "https://puls.apps.radlab.dev", style: primary}
  - {label: "Artykuł o RAG na blogu", href: "/2025-12-26/czy-mozna-w-prosty-sposob-wprowadzic-baze-wiedzy-dla-genai/", style: quiet}
---

## Czym jest Puls Informacji?

**Puls Informacji** (`puls.apps.radlab.dev`) to aplikacja internetowa RadLab udostępniająca funkcje **Kreatora Aktualności** znanego z RDL Playground AI. Zbiera wiadomości z wielu serwisów i tworzy na ich podstawie artykuł na wskazany temat, ograniczając potrzebę samodzielnego przeglądania portali informacyjnych.

Wpisz własne pytanie lub wybierz jeden z proponowanych tematów. Następnie określ styl artykułu (**prosty lub formalny**) oraz zakres wiadomości (**ostatni dzień, 2 dni lub 7 dni**). System przeszuka indeks, zbierze powiązane doniesienia i przygotuje spójny tekst z linkami do źródeł.

---

## Architektura i zasada działania (RAG)

Aplikacja opiera się na wzorcu **RAG (Retrieval-Augmented Generation)**:

```text
[ Pytanie ] → [ Wyszukiwanie w indeksie RadLab ] → [ Wybrane wiadomości ]
                                                           ↓
[ Artykuł + źródła + statystyki ] ← [ Generowanie tekstu przez model AI ]
```

1. **Własny indeks wiadomości:** Aplikacja przeszukuje indeks stron analizowanych przez RadLab, bez korzystania z zewnętrznych API wyszukiwania. Według informacji w aplikacji wiadomości ze Strumienia Aktualności trafiają do indeksu po około 10 minutach.
2. **Generowanie na podstawie źródeł:** Model tworzy artykuł na podstawie wyszukanych wiadomości. Takie podejście ogranicza ryzyko zmyślonych informacji, ale nie wyklucza błędów — istotne fakty warto sprawdzić w podlinkowanych źródłach.
3. **Analiza wydźwięku (Polarity 3C):** Wykres pokazuje udział wiadomości o wydźwięku pozytywnym, negatywnym i ambiwalentnym w wynikach wyszukiwania.
4. **Źródła i statystyki:** Obok artykułu dostępne są linki do źródeł, informacje o modelu i czasie generowania, liczba dopasowanych wiadomości, liczba słów oraz szacowany czas czytania.

---

## Technologie i funkcje

Interfejs aplikacji jest dostosowany do komputerów i urządzeń mobilnych:

* **Next.js 15 (App Router), React 19 i TypeScript:** Interfejs wykorzystuje Tailwind CSS v4, a wykresy powstają w CSS/SVG, bez dodatkowych bibliotek wykresów ani gotowego zestawu komponentów UI.
* **Pośrednictwo po stronie serwera:** Trasy API w Next.js przekazują żądania do usług RadLab. Dzięki temu przeglądarka nie łączy się bezpośrednio z serwerem tych usług.
* **Dwa języki interfejsu:** Polski i angielski.
* **Kopiowanie i eksport:** Gotowy tekst można skopiować do schowka lub pobrać w formacie Markdown (`.md`).

---

## Dostęp do aplikacji

* **Otwórz aplikację:** [puls.apps.radlab.dev](https://puls.apps.radlab.dev).
* **Status:** Wersja demonstracyjna w ekosystemie RadLab.
