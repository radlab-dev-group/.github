---
title: "RDL Playground AI"
subtitle: "Poletko doświadczalne AI do analizy i podsumowywania aktualności"
slug: "playground"
description: "RDL Playground AI to projekt badawczy non-profit pokazujący automatyczną analizę wiadomości: strumień polskich podsumowań, artykuły tworzone w odpowiedzi na pytania i dzienne przeglądy informacji ze źródłami. Działa lokalnie i nie wymaga konta."
icon: "flask"
status: "Platforma Badawcza · Non-Profit"
version: "Live Web App"
tags: ["NLP", "News Stream", "Summarization", "Information Retrieval", "Local Processing"]
actions:
  - {label: "Uruchom Playground (playground.radlab.dev)", href: "https://playground.radlab.dev", style: primary}
  - {label: "Eksperymenty i metody na blogu", href: "/blog/", style: quiet}
---

## Czym jest RDL Playground AI?

**RDL Playground AI** to poletko doświadczalne RadLaba, na którym pokazujemy działanie metod sztucznej inteligencji na wiadomościach z internetu. To projekt badawczy realizowany non-profit, dostępny bez zakładania konta.

Pobieranie treści, ich przetwarzanie, analiza i prezentacja wyników są zautomatyzowane. Człowiek nadzoruje działanie systemu, a dodatkowe metody i modele wspierają tę kontrolę.

---

## Co znajdziesz na Playgroundzie?

### 1. Strumień aktualności
Krótkie podsumowania wiadomości z polskich i zagranicznych portali, prezentowane po polsku niezależnie od języka źródła. System pobiera treści, analizuje je, streszcza i indeksuje do dalszego wyszukiwania.

Przed publikacją podsumowanie musi przejść testy sprawdzające m.in. podobieństwo do oryginału pod kątem plagiatu oraz zgodność tematu z wiadomością źródłową. Strumień pokazuje ostatnie wiadomości, a nie pełne archiwum.

### 2. Kreator aktualności
Zadajesz pytanie dotyczące bieżących informacji, a Kreator przygotowuje artykuł podsumowujący powiązane wiadomości. Możesz wybrać zakres ostatnich **1, 2 lub 3 dni**.

Obok artykułu otrzymujesz listę stron źródłowych oraz statystyki wyników, w tym diagram polaryzacji analizowanych tekstów. Pozwala to wrócić do źródeł i sprawdzić wydźwięk materiałów, na których oparto odpowiedź.

### 3. Przeglądarka informacji
Automatycznie wykrywa tematy obecne w mediach i przedstawia dzienny przegląd najistotniejszych informacji. Analiza dotyczy poprzedniego dnia — nie jest to widok aktualizowany na bieżąco.

Każda informacja ma nazwę, streszczenie opracowane na podstawie próbki danych oraz źródła, z których pochodzi.

---

## Lokalne przetwarzanie i małe modele

Całość rozwiązania działa lokalnie. Analizowane treści nie są wysyłane do serwisów zewnętrznych, a dane z portali newsowych są przechowywane lokalnie i nie służą do komercyjnego wykorzystania.

Playground pokazuje, co można osiągnąć na budżetowym sprzęcie — według opisu projektu do **6,5 tys. zł brutto**. Wykorzystuje małe modele generatywne, do **12 mld parametrów**, mieszczące się na karcie graficznej z **24 GB pamięci**, z miejscem na kontekst. To świadomie przyjęte ograniczenie eksperymentu, a nie prezentacja możliwości największych modeli.

---

## Dostęp i powiązane artykuły na blogu

* **Aplikacja webowa:** [playground.radlab.dev](https://playground.radlab.dev) — bez logowania i opłat.
* **Kulisy inżynierskie i metody na blogu:**
  * [Przeglądarka informacji — jak automatycznie wykrywać tematy w mediach](/2025-05-28/przegladarka-informacji/)
  * [Eksplorator Informacji – nie młotek, a skalpel w analizie powiązań](/2025-07-14/eksplorator-informacji-nie-mlotek-a-skalpel/)
  * [Model polaryzacji 3C udostępniony na Hugging Face](/2025-06-01/polaryzacja-3c-model-z-plg-na-hf/)
  * [Czy można w prosty sposób wprowadzić bazę wiedzy dla GenAI?](/2025-12-26/czy-mozna-w-prosty-sposob-wprowadzic-baze-wiedzy-dla-genai/)
  * [pLLama3.1 8B — średnio-duże a nawet małe GenAI dla Polskiego](/2024-12-08/pllama3-1-8b-czyli-srednio-duze-a-nawet-male-genai-dla-polskiego/)
