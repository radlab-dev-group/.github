---
title: "Semantic Search Engine"
subtitle: "Od własnych dokumentów do wyszukiwania i odpowiedzi AI"
slug: "semantic-search-engine"
description: "Semantic Search Engine łączy zarządzanie dokumentami, wyszukiwanie semantyczne i hybrydowe oraz odpowiedzi RAG. Backend Django REST API i interfejs FastAPI z Jinja2 pozwalają budować i przeszukiwać własne bazy wiedzy."
icon: "data"
status: "Backend API · Interfejs internetowy"
version: "Django · FastAPI · RAG"
tags: ["Semantic Search", "Hybrid Search", "RAG", "Milvus", "PostgreSQL", "Knowledge Base"]
actions:
  - {label: "GitHub — silnik i API", href: "https://github.com/radlab-dev-group/semantic-search-engine", style: primary}
  - {label: "GitHub — interfejs użytkownika", href: "https://github.com/radlab-dev-group/semantic-search-engine-ui", style: quiet}
---

## Czym jest Semantic Search Engine?

**Semantic Search Engine** to zestaw narzędzi do budowania bazy wiedzy na podstawie własnych dokumentów. Pozwala przygotować i zaindeksować treści, wyszukiwać fragmenty według znaczenia pytania oraz generować odpowiedzi z wykorzystaniem odnalezionych materiałów — w modelu **RAG (Retrieval-Augmented Generation)**.

Produkt składa się z dwóch współpracujących części: **silnika z REST API** oraz **interfejsu internetowego**. Można korzystać z gotowego panelu lub zintegrować backend z własną aplikacją; repozytorium silnika zawiera również klienta Python `sse_lib`.

---

## Do czego służy?

* **Przeszukiwanie dokumentacji i materiałów wewnętrznych:** Znajduj powiązane fragmenty także wtedy, gdy pytanie używa innych słów niż dokument.
* **Bazy wiedzy dla zespołów:** Organizuj treści w kolekcje, przeglądaj dokumenty i decyduj, które z nich mają uczestniczyć w wyszukiwaniu.
* **Asystenci korzystający ze źródeł:** Buduj odpowiedzi na podstawie wyszukanych fragmentów zamiast polegać wyłącznie na wiedzy modelu.
* **Eksperymenty z wyszukiwaniem i RAG:** Dobieraj modele embeddingowe, rerankery, filtry i parametry generowania; wracaj do historii zapytań i zbieraj oceny odpowiedzi.

---

## Najważniejsze możliwości

* **Import plików lub wklejonego tekstu:** Interfejs obsługuje PDF, DOCX, TXT, HTML, Markdown i archiwa ZIP. Treści są przygotowywane do indeksowania i dzielone na fragmenty.
* **Kontrola podziału tekstu:** Ustaw rozmiar fragmentów i nakładanie się ich treści dla kolekcji. Panel uwzględnia limit długości wybranego modelu embeddingowego.
* **Zarządzanie bazą wiedzy:** Twórz i usuwaj kolekcje, przeglądaj treść dokumentów, usuwaj fragmenty oraz włączaj lub wyłączaj dokumenty w wynikach wyszukiwania.
* **Widoczny postęp indeksowania:** Sprawdzaj dokumenty przetworzone, oczekujące i zakończone błędem. Backend może indeksować w żądaniu lub opcjonalnie przez kolejkę Celery z RabbitMQ.
* **Wyszukiwanie semantyczne i hybrydowe:** Wyszukiwanie wektorowe w Milvus można połączyć z pełnotekstowym w PostgreSQL za pomocą RRF (Reciprocal Rank Fusion). Opcjonalny reranker ponownie porządkuje wyniki względem pytania.
* **Filtry i modele:** Zawężaj wyszukiwanie m.in. do kategorii i dokumentów oraz korzystaj ze skonfigurowanych modeli embeddingowych, rerankerów i modeli generatywnych.
* **Odpowiedzi RAG i informacja zwrotna:** Najpierw przeglądaj wyniki wyszukiwania, a następnie odpowiedź modelu, doczytywaną asynchronicznie. Oceniaj odpowiedzi gwiazdkami i komentarzem oraz wracaj do zapisanych wyszukiwań w kolekcji.
* **Interfejs PL i EN:** Panel oferuje przełączanie języka oraz motyw jasny, ciemny i automatyczny. Zasoby interfejsu są lokalne, bez zależności od zewnętrznych CDN.

---

## Architektura i technologie

```text
Przeglądarka → Interfejs FastAPI + Jinja2 → REST API Django
                                               ├─ PostgreSQL: dokumenty, metadane i wyszukiwanie tekstowe
                                               ├─ Milvus: indeks wektorowy
                                               ├─ Modele embeddingowe i rerankery
                                               └─ Modele generatywne: odpowiedzi RAG
```

**Backend** wykorzystuje Python, Django i Django REST Framework. PostgreSQL przechowuje dane relacyjne, a Milvus umożliwia wyszukiwanie wektorowe. Modele embeddingowe i rerankery służą do dopasowywania treści; skonfigurowany model generatywny przygotowuje odpowiedź na podstawie wyników.

**Interfejs** jest osobną aplikacją Python opartą na FastAPI i szablonach Jinja2, z lokalnymi plikami CSS i JavaScript. Komunikuje się z silnikiem przez REST API i obsługuje logowanie z użyciem tokenu backendu. Nie wymaga frameworka SPA.

System można uruchomić we własnej infrastrukturze. Zakres komunikacji z usługami zewnętrznymi zależy od konfiguracji modeli i integracji — lokalny interfejs nie oznacza automatycznie lokalnego przetwarzania wszystkich danych. Trafność wyników i jakość odpowiedzi zależą od dokumentów, podziału tekstu oraz wybranych modeli; odpowiedzi AI nadal wymagają weryfikacji.

---

## Kod i dokumentacja

* **Silnik, API i klient Python:** [semantic-search-engine](https://github.com/radlab-dev-group/semantic-search-engine).
* **Panel użytkownika i instrukcja uruchomienia:** [semantic-search-engine-ui](https://github.com/radlab-dev-group/semantic-search-engine-ui).