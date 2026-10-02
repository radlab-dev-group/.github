## 🚀 Roadmap Projektu **LLM‑Router**

### 📍 Poziom 1 – **Dev / Test**

**Aktualny etap** – wprowadzamy podstawowe funkcje i integracje.

| Zadanie                                                               | Cel                                                              | Status    |
|-----------------------------------------------------------------------|------------------------------------------------------------------|-----------|
| Dokończenie integracji z **LM Studio**                                | Pełna obsługa modeli lokalnych                                   | ✅ gotowe  |
| Strumieniowy zwrot **guardrails**                                     | Odpowiedź zwracana jako strumień, a nie jednorazowo              | ✅ gotowe  |
| Integracja z natywnym API **Anthropic**                               | Obsługa Anthropic poza warstwą OpenAI                            | ✅ gotowe  |
| Rozszerzenie reguł maskowania (EN, US)                                | Lepsza ochrona danych w językach angielskim i amerykańskim       | 🔄 w toku |
| Dodanie serwisu **guardrails** typu *prompt injection*                | Wykrywanie i blokowanie niepożądanych promptów                   | 🔄 w toku |
| Uaktualnienie frontendu **ConfigsManager** i **Anonimizera** (+ chat) | Przyjazny interfejs do zarządzania konfiguracjami i anonimizacją | 🔄 w toku |
| Obsługa API **RAG‑style** (embeddings)                                | Wsparcie dla aplikacji typu RAG do obsługi embeddingów           | ✅ gotowe  |

---

### 📍 Poziom 2 – **Prod**

**Wprowadzenie LLM‑Routera** jako elementu rozporoszonego ekosystemu produkcyjnego.

| Obszar             | Inicjatywa                                                                       | Opis                                                      |
|--------------------|----------------------------------------------------------------------------------|-----------------------------------------------------------|
| **Skalowalność**   | Rozwiązania umożliwiające wyskalowanie LLM‑Routera do bardzo specyficznych zadań | Modularna architektura, autoskalowanie w lokalnej chmurze |
| **Bezpieczeństwo** | Mechanizmy oparte na komunikacji w **Kafka** (kolejkowanie zadań)                | Izolacja zadań, monitorowanie i retry‑policy              |
| **Agentowość**     | Integracja z lokalnymi systemami agentowymi                                      | Współpraca z lokalnymi agentami np. kodującymi            |

---

### 📍 Poziom 3 – **Pain**

**Rozwiązywanie kluczowych problemów biznesowych**.

| Kategoria                           | Działanie                                                                                             | Korzyść                                                                |
|-------------------------------------|-------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------|
| **Bezpieczeństwo i ochrona danych** | Integracja z systemami **SIEM** (Security Information & Event Management)                             | Wczesne wykrywanie incydentów i pełna audytowalność                    |
| **Skalowalność**                    | Wprowadzenie **llm‑router‑node** jako warstwy działającej w różnych podsieciach (integrator routerów) | Rozproszone przetwarzanie, integracja podsieci, zwiększenie wydajności |
| **Przesyłanie dokumentów**          | Bezpieczne przesyłanie dokumentów w aplikacjach webowych (API + WEB)                                  | Warstwa dbająca o bezpieczeństwo dokumentów, pełna audytowalność       |

---

### 📍 Poziom 4 – **Future**

**Długoterminowe, projekty badawcze** – budujemy najnowocześniejsze rozwiązania.

| Projekt                                        | Opis                                                       | Potencjalny wpływ                                             |
|------------------------------------------------|------------------------------------------------------------|---------------------------------------------------------------|
| **llm‑router‑grpc**                            | Protokół RPC do rozgłaszania zadań w zaufanych podsieciach | Ultra‑niskie opóźnienia, efektywna komunikacja między węzłami |
| **llm‑router‑protocol**                        | Komunikacja oparta na **blockchain**                       | Niezmienność, transparentność i odporność na manipulacje      |
| **Integracja LLM‑Routera z gRPC i blockchain** | Najbezpieczniejsze rozwiązanie do przesyłania informacji   | Kompleksowe zabezpieczenia, audytowalny przepływ danych       |

---

### 🎯 Podsumowanie

Roadmapa jasno wyznacza kolejne etapy rozwoju od **pilotażowego środowiska testowego** po **globalne, badawcze innowacje
**. Każdy poziom skupia się na konkretnych priorytetach – od integracji i podstawowej funkcjonalności, przez
skalowalność i bezpieczeństwo w produkcji, po zaawansowane rozwiązania chroniące dane i umożliwiające rozproszone
przetwarzanie. Dzięki temu projekt ma solidne fundamenty, a jednocześnie pozostaje otwarty na przyszłe, przełomowe
technologie.