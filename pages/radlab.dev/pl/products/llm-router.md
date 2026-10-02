---
title: "LLM Router"
subtitle: "Otwarta brama AI do zarządzania ruchem między modelami językowymi"
slug: "llm-router"
description: "LLM Router to brama AI uruchamiana we własnej infrastrukturze. Udostępnia interfejs zgodny z OpenAI oraz endpoint Anthropic dla lokalnych silników i zewnętrznych API, z konfigurowalnymi wtyczkami, ochroną danych i równoważeniem obciążenia."
icon: "router"
status: "Open Source · Apache-2.0"
version: "v1.1.6"
tags: ["AI Gateway", "vLLM", "Ollama", "PII Masking", "Load Balancing", "Guardrails", "Self-Hosted"]
actions:
  - {label: "Strona projektu (llm-router.cloud)", href: "https://llm-router.cloud", style: primary}
  - {label: "GitHub (radlab-dev-group)", href: "https://github.com/radlab-dev-group/llm-router", style: quiet}
  - {label: "Dokumentacja techniczna", href: "https://llm-router.cloud/docs/", style: quiet}
---

## Czym jest LLM Router?

**LLM Router** to otwarta brama AI uruchamiana we własnej infrastrukturze — na serwerach lokalnych, w prywatnej chmurze lub w środowisku odciętym od sieci. Stoi pomiędzy aplikacjami a skonfigurowanymi przez Ciebie dostawcami modeli.

Aplikacje korzystają z jednego interfejsu zgodnego z **OpenAI API** lub natywnego endpointu **Anthropic `/v1/messages`**. Router przekazuje zapytania do lokalnych silników, takich jak **vLLM**, **Ollama**, **llama.cpp** i **LM Studio**, oraz do skonfigurowanych API zewnętrznych. Po drodze może stosować autoryzację, maskowanie danych, guardraile i wybrane reguły kierowania ruchu. Etapy potoku włącza się w konfiguracji.

---

## Kluczowe możliwości

### 1. Jeden interfejs do modeli
Router obsługuje m.in. endpointy `/v1/chat/completions`, `/v1/responses` i `/v1/embeddings`, a także `/v1/messages` dla klientów Anthropic. Odpowiedzi mogą być przesyłane strumieniowo przez SSE. Modele, dostawców oraz działanie routera określa się w pliku konfiguracyjnym i zmiennych środowiskowych.

### 2. Konfigurowalny potok wtyczek
Wtyczki pozwalają włączać i układać etapy przetwarzania zapytań bez zmiany kodu aplikacji:

* **Maskowanie PII:** `fast_masker` stosuje reguły dla identyfikatorów i danych kontaktowych; `pii_masker` może dodatkowo użyć klasyfikatora ML.
* **Guardraile:** Wtyczki `nask_guard` i `sojka_guard` sprawdzają zapytanie przed wywołaniem modelu.
* **Routing semantyczny:** Dla `model: "auto"` można włączyć wtyczkę dobierającą model na podstawie treści zapytania.
* **Rozszerzenia:** Potok można uzupełnić o własne wtyczki, w tym wzbogacanie kontekstu z bazy wiedzy.

### 3. Strategie równoważenia obciążenia
Strategia wybiera **dostawcę wskazanego modelu**, gdy ten ma więcej niż jednego dostawcę:

1. **`balanced` (domyślna):** Wybiera dostawcę, który dotąd obsłużył najmniej zapytań dla danego modelu.
2. **`weighted`:** Rozdziela ruch według skonfigurowanych, stałych wag dostawców.
3. **`dynamic_weighted` (beta):** Dostosowuje wagi z uwzględnieniem obserwowanych opóźnień.
4. **`first_available`:** Przydziela pierwszego dostępnego dostawcę na wyłączność; wymaga Redis do koordynacji między workerami.
5. **`first_available_optim`:** Preferuje hosty, na których model był już uruchomiony, aby ograniczyć ponowne ładowanie; korzysta z Redis.
6. **`first_available_optim_nworkers`:** Pozwala przydzielić dostawcy do `nworkers` równoległych zapytań i wybiera dostawcę z najmniejszą liczbą zajętych slotów; sloty są koordynowane w Redis.

Pełne zachowanie i wymagania opisuje [dokumentacja strategii balansowania](https://github.com/radlab-dev-group/llm-router/blob/main/llm_router_api/docs/LB_STRATEGIES.md).

### 4. Dostępność i kontrola ruchu
* **Obsługa błędów dostawców:** Router próbuje kolejnych dostawców **tego samego modelu**. Dopiero gdy nie może on obsłużyć zapytania, można użyć skonfigurowanego osobno `fallback_model`. Nie jest to strategia balansowania ani automatyczne przełączanie na chmurę.
* **Klucze i limity:** Autoryzacja opiera się na kluczach z uprawnieniami do endpointów; limity zapytań działają w oknie przesuwnym z użyciem Redis dla klucza i adresu IP.

### 5. Obserwowalność i audyt
* **Prometheus:** Po włączeniu `/metrics` udostępnia liczniki wywołań, błędów, ponowień i tokenów oraz histogramy opóźnień dostawców.
* **Audyt GPG:** Można zapisywać zaszyfrowane wpisy o decyzjach maskowania i guardraili.

---

## Architektura systemu

```text
[ Twoje Aplikacje / Agenci AI ]
             │ (OpenAI / Anthropic API format)
             ▼
   ┌────────────────────────────────────────────────────────┐
   │                     LLM ROUTER                         │
   │                                                        │
   │  ┌──────────────────────────────────────────────────┐  │
   │  │ Pre-inference Pipeline                           │  │
   │  │ ├─ Auth & Rate Limiting (opcjonalnie)             │  │
   │  │ ├─ Maskowanie PII                                 │  │
   │  │ └─ Guardraile i routing semantyczny               │  │
   │  └────────────────────────┬─────────────────────────┘  │
   │                           ▼                            │
   │  ┌──────────────────────────────────────────────────┐  │
   │  │ Routing Engine & Load Balancer                   │  │
   │  │ (np. balanced · weighted · first_available)      │  │
   │  └────────────┬────────────────────────┬────────────┘  │
   └───────────────┼────────────────────────┼───────────────┘
                   ▼                        ▼
       [ Silniki lokalne GPU ]    [ Dostawcy chmurowi ]
       ├─ vLLM                    ├─ OpenAI
       ├─ Ollama                  └─ Anthropic
       └─ LM Studio / llama.cpp
```

---

## Zasoby i dokumentacja

* **Oficjalna strona projektu:** [llm-router.cloud](https://llm-router.cloud)
* **Repozytorium GitHub:** [radlab-dev-group/llm-router](https://github.com/radlab-dev-group/llm-router)
* **Ekosystem wtyczek:** [radlab-dev-group/llm-router-plugins](https://github.com/radlab-dev-group/llm-router-plugins)
* **Licencja:** Apache 2.0 (dozwolone zastosowania komercyjne i niekomercyjne)
