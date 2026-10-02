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

## Szybki start (Quickstart)

LLM Router można uruchomić jako kontener Docker i podłączyć do klienta OpenAI przez zmianę `base_url`. Obsługa konkretnych funkcji API zależy również od wybranego dostawcy modelu.

### 1. Uruchomienie kontenera

Przykład zakłada działający na hoście serwer vLLM na porcie `8000`, udostępniający model pod nazwą `llama-3.1-8b`. Router nie uruchamia modelu za Ciebie. Zapisz jako `config.json`:

```json
{
  "local_models": {
    "llama-3.1-8b": {
      "providers": [{
        "id": "local-vllm",
        "api_host": "http://host.docker.internal:8000/",
        "api_token": "",
        "api_type": "vllm",
        "model_path": "llama-3.1-8b",
        "input_size": 4096,
        "weight": 1.0,
        "nworkers": 1
      }]
    }
  },
  "active_models": {"local_models": ["llama-3.1-8b"]}
}
```

```bash
docker run -d \
  --name llm-router \
  -p 127.0.0.1:5555:8080 \
  --add-host=host.docker.internal:host-gateway \
  -e LLM_ROUTER_SERVER_PORT=8080 \
  -e LLM_ROUTER_MODELS_CONFIG=/srv/cfg.json \
  -v "$(pwd)/config.json:/srv/cfg.json:ro" \
  quay.io/radlab/llm-router:rc1
```

Tag `rc1` i zmienne pochodzą z [instrukcji Docker w repozytorium](https://github.com/radlab-dev-group/llm-router#-docker). Model musi być osiągalny z kontenera; na Linuksie backend nasłuchujący wyłącznie na `127.0.0.1` nie wystarczy. Przykład bramy jest dostępny tylko lokalnie; przed udostępnieniem jej w sieci włącz autoryzację i TLS zgodnie z [dokumentacją uwierzytelniania](https://github.com/radlab-dev-group/llm-router/blob/main/llm_router_api/docs/AUTHENTICATION.md).

### 2. Integracja w Pythonie (OpenAI SDK)

```python
from openai import OpenAI

# Wystarczy podmienić base_url na adres bramy LLM Router
client = OpenAI(
    base_url="http://localhost:5555/v1",
    api_key="twoj-klucz-api"  # lub dowolny ciąg przy wyłączonej autoryzacji
)

response = client.chat.completions.create(
    model="llama-3.1-8b",
    messages=[
        {"role": "system", "content": "Jesteś pomocnym asystentem inżynierskim."},
        {"role": "user", "content": "Jak skonfigurować bezpieczny routing zapytań LLM?"}
    ],
    temperature=0.7,
    stream=True
)

for chunk in response:
    if chunk.choices and chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

### 3. Zapytanie przez cURL

```bash
curl http://localhost:5555/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer twoj-klucz-api" \
  -d '{
    "model": "llama-3.1-8b",
    "messages": [
      {"role": "user", "content": "Cześć! Opowiedz krótko o architekturze routera."}
    ]
  }'
```

---

## Porównanie z alternatywami (Differentiators)

| Cecha / Funkcjonalność | LLM Router | LiteLLM | Ollama (standalone) | Portkey / Cloud Gateways |
| :--- | :--- | :--- | :--- | :--- |
| **Model wdrożenia** | Self-hosted; air-gapped z lokalnymi modelami i zależnościami | Self-hosted / usługi zarządzane | Lokalny serwer modeli | Otwarta brama self-hosted / platforma SaaS |
| **Maskowanie PII i guardraile** | Konfigurowalne wtyczki FastMasker, RoBERTa NER, NASK Guard i Sójka Guard dla polskiego | Integracje guardraili, m.in. Presidio; zakres zależy od integracji i edycji | Wymaga dodatkowej warstwy aplikacji | Integracje guardraili; zakres zależy od wdrożenia i planu |
| **Routing i Load Balancing** | 6 strategii; m.in. wagi, sloty workerów i koordynacja Redis | Strategie losowe/ważone, latencja, użycie i least-busy | Obsługuje własny serwer, nie zastępuje bramy wielu dostawców | Load balancing, fallback i routing warunkowy |
| **Obsługa standardów API** | OpenAI-compatible + Anthropic `/v1/messages` | Ujednolicone API OpenAI-compatible dla wielu dostawców | Ollama API / zgodność z częścią OpenAI API | Ujednolicone API dla wielu dostawców |
| **Obserwowalność i audyt** | Opcjonalny Prometheus `/metrics` i szyfrowany audyt GPG | Metryki, logowanie i śledzenie kosztów | Logi serwera | Funkcje obserwowalności platformy zależne od planu |
| **Licencja** | Apache 2.0 | Rdzeń MIT; funkcje enterprise na osobnych warunkach | MIT | Otwarta brama MIT; platforma komercyjna osobno |

Wyróżnikiem LLM Routera jest zestaw polskich wtyczek i kontrola nad lokalną infrastrukturą, nie wyłączność na routing czy self-hosting. Porównanie dotyczy modelu działania, nie benchmarku wydajności. Źródła: [LLM Router](https://github.com/radlab-dev-group/llm-router), [routing LiteLLM](https://docs.litellm.ai/docs/routing), [brama Portkey](https://github.com/Portkey-AI/gateway), [zgodność API Ollama](https://docs.ollama.com/api/openai-compatibility).

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
