---
title: "RDL Playground AI"
subtitle: "Interaktywne środowisko badawcze i piaskownica testowa dla modeli językowych i agentów NLP"
slug: "playground"
description: "RDL Playground AI to otwarta platforma badawczo-demonstracyjna RadLab. Umożliwia bezpośrednie testowanie polskich modeli z rodziny pLLama, klasyfikatorów sentymentu, analizy strumieni wiadomości oraz agentów AI w praktycznych zadaniach przetwarzania języka naturalnego."
icon: "flask"
status: "Platforma Badawcza · Non-Profit"
version: "Live Web App"
tags: ["Playground AI", "pLLama Models", "Public Chat", "Polarity 3C", "News Stream", "NLP Research"]
actions:
  - {label: "Uruchom Playground (playground.radlab.dev)", href: "https://playground.radlab.dev", style: primary}
  - {label: "Modele na Hugging Face", href: "https://huggingface.co/radlab", style: quiet}
  - {label: "Wpisy i raporty na blogu", href: "/blog/", style: quiet}
---

## Czym jest RDL Playground AI?

**RDL Playground AI** to publiczna piaskownica technologiczna stworzona przez zespół RadLab w celu praktycznej weryfikacji i demonstracji modeli językowych, klasyfikatorów oraz agentów przetwarzania języka naturalnego (NLP) dla języka polskiego.

Platforma powstała jako pomost między pracami badawczo-rozwojowymi (R&D) a gotowymi aplikacjami produkcyjnymi. Pozwala inżynierom, analitykom i badaczom „dotknąć” technologii i sprawdzić, jak modele radzą sobie z polską fleksją, niuansami kontekstowymi oraz dużymi strumieniami nieustrukturyzowanych danych.

---

## Główne moduły i eksperymenty

```text
┌─────────────────────────────────────────────────────────────────┐
│                       RDL PLAYGROUND AI                         │
├────────────────────┬────────────────────┬───────────────────────┤
│  Czat Publiczny    │ Strumień Newsów    │ Przeglądarka /        │
│  & Agenci          │ & Polaryzacja 3C   │ Eksplorator Wiedzy    │
│  ├─ pLLama 1B-70B  │ ├─ Live Ingestion  │ ├─ Klastrowanie newsów│
│  └─ Supervisor     │ └─ Sentyment       │ └─ Grafy relacji      │
└────────────────────┴────────────────────┴───────────────────────┘
```

### 1. Czat Publiczny i Agenci AI
* **Wnioskowanie na modelach pLLama:** Możliwość prowadzenia dialogu z modelami generatywnymi dostrojonymi do języka polskiego (od lekkich modeli brzegowych 1B/3B po zaawansowane warianty 8B i 70B).
* **Nadzorca treści (Content Supervisor):** Wbudowane mechanizmy agentowe weryfikujące poprawność merytoryczną, halucynacje i zgodność odpowiedzi z podanym kontekstem.
* **Wymiana sesji (Chat Hashes):** Możliwość dzielenia się zapisanymi sesjami konwersacji za pomocą unikalnych skrótów kryptograficznych.

### 2. Strumień Aktualności i Polaryzacja (Polarity 3C)
* **Monitoring na żywo:** Ciągły napływ artykułów z ogólnopolskich i branżowych portali internetowych.
* **Klasyfikacja wydźwięku 3C:** Każdy napływający tekst jest w czasie rzeczywistym oceniany przez dedykowany model RoBERTa `radlab/polarity-3c` pod kątem ładunku emocjonalnego:
  * **Pozytywny:** Treści niosące konstruktywny, optymistyczny przekaz.
  * **Negatywny:** Informacje o kryzysach, problemach czy konfliktach.
  * **Ambiwalentny / Neutralny:** Czyste fakty lub teksty o zrównoważonych, przeciwstawnych emocjach.

### 3. Przeglądarka i Eksplorator Informacji
* **Odkrywanie trendów bez sztywnych kategorii:** Automatyczna agregacja tysięcy newsów w zwarte klastry tematyczne.
* **Grafy relacji informacyjnych:** Narzędzie badawcze (oparte na raportach technicznych RadLab) mapujące powiązania pomiędzy wydarzeniami, osobami i źródłami medialnymi.
* **Wizualizacja propagacji:** Śledzenie, które źródła rozpoczęły dyskusję na dany temat i jak informacja rozprzestrzeniała się w czasie.

### 4. Statystyki i Obserwatorium Danych
* Przejrzyste wykresy prezentujące dzienne rozkłady emocji w mediach, wolumen przetwarzanych tekstów oraz metryki efektywności modeli.

---

## Architektura i zaplecze technologiczne

Playground jest zasilany przez własny ekosystem narzędzi RadLab:
* **Silnik routingu:** Wszystkie zapytania do modeli przechodzą przez instancję **LLM Routera**, który odpowiada za kolejkowanie, równoważenie obciążenia i streaming odpowiedzi.
* **Wnioskowanie:** Lokalne środowiska GPU wykorzystujące **vLLM** oraz zoptymalizowane kwantyzacje.
* **Modele Open Source:** Wagi modeli używanych w Playgroundzie są publicznie udostępniane na naszym profilu Hugging Face.

---

## Otwarty dostęp

RDL Playground AI jest w pełni otwarty dla społeczności naukowej i inżynierskiej:
* Bez konieczności tworzenia konta czy podawania danych karty,
* Bez reklam i monetyzacji danych użytkowników,
* Dostępny pod adresem: **[playground.radlab.dev](https://playground.radlab.dev)**
