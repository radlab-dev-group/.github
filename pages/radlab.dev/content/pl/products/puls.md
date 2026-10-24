---
title: "Puls Informacji"
subtitle: "Wiadomości z wielu źródeł zebrane w jeden artykuł na wybrany temat"
slug: "puls"
description: "Puls Informacji to aplikacja internetowa RadLab, która tworzy artykuły w odpowiedzi na pytania o bieżące wydarzenia. Korzysta z własnego indeksu wiadomości z wielu serwisów, dołącza linki do źródeł i przedstawia analizę wydźwięku wyszukanych tekstów."
icon: "spark"
status: "Aplikacja internetowa · Wersja demonstracyjna"
version: "Flask · RAG"
tags: ["RAG", "Generative AI", "Information Synthesis", "News Search", "Polarity 3C", "Local Index"]
actions:
  - {label: "Otwórz aplikację (puls.apps.radlab.dev)", href: "https://puls.apps.radlab.dev", style: primary}
  - {label: "Artykuł o RAG na blogu", href: "/2025-12-26/czy-mozna-w-prosty-sposob-wprowadzic-baze-wiedzy-dla-genai/", style: quiet}
---

## Czym jest Puls Informacji?

**Puls Informacji** (`puls.apps.radlab.dev`) to aplikacja internetowa RadLab udostępniająca funkcje **Kreatora Aktualności** znanego z RDL Playground AI. Zbiera wiadomości z wielu serwisów i tworzy na ich podstawie artykuł na wskazany temat, ograniczając potrzebę samodzielnego przeglądania portali informacyjnych.

Wpisz własne pytanie lub wybierz jeden z proponowanych tematów. Następnie określ styl artykułu (**prosty lub formalny**) oraz zakres wiadomości (**ostatni dzień, 2 dni lub 7 dni**). System przeszuka indeks, zbierze powiązane doniesienia i przygotuje spójny tekst z linkami do źródeł.

---

## Do czego służy Puls?

* **Codzienny przegląd aktualności:** Zbierz doniesienia na interesujący Cię temat w jeden tekst, zamiast otwierać kolejne portale.
* **Rozeznanie przed spotkaniem lub dalszą lekturą:** Przygotuj punkt wyjścia do poznania bieżących wydarzeń w branży, technologii czy życiu publicznym, a następnie przejdź do materiałów źródłowych.
* **Przegląd ostatnich dni:** Wybierz zakres 1, 2 lub 7 dni, aby zebrać najświeższe doniesienia albo spojrzeć na temat w szerszym kontekście.
* **Materiał do własnych notatek:** Dobierz prosty lub formalny styl, skopiuj wynik albo zapisz go w Markdown i wykorzystaj jako punkt wyjścia do dalszej pracy.

Puls nie zastępuje redakcyjnej weryfikacji ani pełnego przeglądu internetu. Zakres odpowiedzi zależy od wiadomości dostępnych w indeksie i wyników ich dopasowania do pytania.

---

## Architektura i zasada działania (RAG)

Aplikacja wykorzystuje **Python i Flask** do renderowania interfejsu z szablonów **Jinja2** oraz pośredniczenia w komunikacji z **backendem RadLab**. Statyczny JavaScript obsługuje interakcje w przeglądarce, a wyszukiwanie i generowanie odbywają się w usługach RadLab. Całość wykorzystuje wzorzec **RAG (Retrieval-Augmented Generation)** — model otrzymuje wiadomości znalezione dla konkretnego zapytania.

```text
Przeglądarka → API aplikacji Flask → Backend RadLab
                                      ├─ Kategorie i dostępne serwisy
                                      ├─ Wyszukiwanie w indeksie wiadomości
                                      └─ Generowanie artykułu z dopasowanych newsów
Przeglądarka ← Artykuł, materiały źródłowe i metadane
```

1. **Własny indeks wiadomości:** Aplikacja przeszukuje indeks stron analizowanych przez RadLab, bez korzystania z zewnętrznych API wyszukiwania. Według informacji w aplikacji wiadomości ze Strumienia Aktualności trafiają do indeksu po około 10 minutach.
2. **Generowanie na podstawie źródeł:** Model tworzy artykuł na podstawie wyszukanych wiadomości. Takie podejście ogranicza ryzyko zmyślonych informacji, ale nie wyklucza błędów — istotne fakty warto sprawdzić w podlinkowanych źródłach.
3. **Analiza wydźwięku (Polarity 3C):** Wykres pokazuje udział wiadomości o wydźwięku pozytywnym, negatywnym i ambiwalentnym w wynikach wyszukiwania.
4. **Źródła i statystyki:** Obok artykułu dostępne są linki do źródeł, informacje o modelu i czasie generowania, liczba dopasowanych wiadomości, liczba słów oraz szacowany czas czytania.

Po otwarciu strony interfejs pobiera kategorie i listę dostępnych serwisów — wszystkie są objęte wyszukiwaniem. Następnie wysyła pytanie i wybrany zakres czasowy do usługi wyszukiwania. Identyfikatory dopasowanych wiadomości trafiają do osobnego żądania generowania wraz z pytaniem i instrukcją stylu. Jeśli wyszukiwanie nie zwróci materiałów, aplikacja informuje o ich braku, zamiast uruchamiać generowanie.

---

## Technologie i funkcje

Interfejs aplikacji jest dostosowany do komputerów i urządzeń mobilnych:

* **Python, Flask i Jinja2:** Serwer renderuje szablony interfejsu, a lokalne pliki CSS i JavaScript odpowiadają za wygląd oraz interakcje. Aplikacja nie wymaga Node.js, Reacta ani etapu kompilacji zasobów frontendu.
* **Pośrednictwo po stronie serwera:** Endpointy Flask komunikują się z usługami RadLab za pomocą biblioteki Requests. Dzięki temu przeglądarka nie łączy się bezpośrednio z serwerem tych usług. Aplikacja przygotowuje też HTML artykułu z Markdown oraz statystyki tekstu po stronie Pythona.
* **Dwa języki interfejsu:** Polski i angielski.
* **Kopiowanie i eksport:** Gotowy tekst można skopiować do schowka lub pobrać w formacie Markdown (`.md`).
* **Przejrzysty zakres wyszukiwania:** Rozwijany panel pokazuje kategorie i serwisy dostępne w indeksie, a sekcja pod artykułem przedstawia konkretne wiadomości użyte do jego przygotowania.
* **Dwa widoki materiałów źródłowych:** Przegląd kart lub zwarta lista, filtrowanie po kategorii, fragmenty wiadomości, daty pobrania i odnośniki do oryginałów ułatwiają dalszą lekturę.
* **Podpowiedzi tematów i ponowne generowanie:** Można wylosować kolejne propozycje pytań, edytować zapytanie i przygotować nowy artykuł. Interfejs pokazuje etap wyszukiwania i generowania; przygotowanie tekstu może potrwać 1–2 minuty.

---

## Dostęp do aplikacji

* **Otwórz aplikację:** [puls.apps.radlab.dev](https://puls.apps.radlab.dev).
* **Status:** Wersja demonstracyjna w ekosystemie RadLab.
