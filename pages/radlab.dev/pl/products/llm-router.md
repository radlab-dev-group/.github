---
title: "LLM Router"
subtitle: "Wydajna brama AI (AI Gateway) open-source i warstwa kontrolna modeli językowych"
slug: "llm-router"
description: "LLM Router to brama AI typu self-hosted dla infrastruktury on-premise i chmurowej. Udostępnia ujednolicony interfejs OpenAI i Anthropic przed silnikami vLLM, Ollama, LM Studio oraz API chmurowymi z maskowaniem PII, guardrailami, routingiem i load balancingiem."
icon: "router"
status: "Open Source · Apache-2.0"
version: "v0.2.3"
tags: ["AI Gateway", "vLLM", "Ollama", "PII Masking", "Load Balancing", "Guardrails", "Self-Hosted"]
actions:
  - {label: "Strona projektu (llm-router.cloud)", href: "https://llm-router.cloud", style: primary}
  - {label: "GitHub (radlab-dev-group)", href: "https://github.com/radlab-dev-group/llm-router", style: quiet}
  - {label: "Dokumentacja techniczna", href: "https://llm-router.cloud/docs/0.2.3/overview.html", style: quiet}
---

## Czym jest LLM Router?

**LLM Router** to wysokowydajna, otwarta brama dostępowa (AI Gateway & Control Plane), którą uruchamiasz wewnątrz własnej infrastruktury — na serwerach on-premise, w prywatnej chmurze lub w środowisku air-gapped. 

Aplikacje biznesowe i mikroserwisy komunikują się z jednym, stabilnym punktem końcowym zgodnym ze standardami **OpenAI API** oraz **Anthropic API**. Router odpowiada za inteligentne przekazywanie zapytań do lokalnych silników wnioskowania (**vLLM**, **Ollama**, **LM Studio**) lub zewnętrznych dostawców chmurowych (**OpenAI**, **Anthropic**, **Groq**, **Mistral**), jednocześnie egzekwując polityki bezpieczeństwa, anonimizację danych i kontrolę kosztów.

---

## Kluczowe możliwości

### 1. Ujednolicony interfejs API
* **Kompatybilność drop-in:** Pełna obsługa formatów `/v1/chat/completions`, `/v1/completions`, `/v1/embeddings` oraz `/v1/models`. Możesz podmienić adres URL w istniejącym kodzie Pythona, TypeScriptu czy Go bez przepisywania logiki aplikacji.
* **Streaming bez opóźnień:** Bezpośrednia obsługa Server-Sent Events (SSE) z narzutem przetwarzania poniżej 2 ms.
* **Formatowanie strukturalne:** Wsparcie dla JSON Schema, wymuszania gramatyk oraz wywoływania funkcji (Tool Calling / Function Calling).

### 2. Deterministyczny potok wtyczek (Plugin Pipeline)
LLM Router przetwarza każde zapytanie w deterministycznym łańcuchu kroków przed wysłaniem go do modelu (*pre-inference*) oraz po odebraniu odpowiedzi (*post-inference*):

* **Wielowarstwowa ochrona PII:** Automatyczne wykrywanie i maskowanie danych osobowych (PESEL, NIP, numery kart płatniczych, adresy, emaile) przed wysyłką do zewnętrznych modeli.
* **Guardraile bezpieczeństwa:** Wykrywanie prób wstrzykiwania promptów (Prompt Injection), filtrowanie niedozwolonych treści oraz blokowanie wycieku tajemnic firmowych (kluczy API, tokenów).
* **RAG Enrichment:** Dynamiczne wzbogacanie promptów o kontekst z baz wiedzy lub wektorowych baz danych w locie.

### 3. 6 zaawansowanych strategii Load Balancingu
LLM Router umożliwia precyzyjne sterowanie ruchem pomiędzy instancjami modeli:
1. **Round Robin:** Równomierny podział zapytań między instancje.
2. **Least Connections:** Kierowanie ruchu do węzła o najmniejszej liczbie aktywnych połączeń.
3. **Latency-Aware:** Dynamiczny routing do instancji o najniższym czasie odpowiedzi (EMA latency).
4. **Priority Failover:** Domyślne kierowanie zapytań do taniego modelu lokalnego (vLLM/Ollama) i automatyczny fallback do chmury w razie awarii lub przeciążenia.
5. **Random Balancing:** Statystyczny rozkład obciążenia z wagami.
6. **Distributed Redis Leasing:** Rezerwacja slotów i równoważenie obciążenia w klastrach wieloinstancyjnych.

### 4. Niezawodność i kontrola ruchu
* **Distributed Rate Limiting:** Ograniczanie liczby zapytań i tokenów (Token Bucket / Fixed Window) na poziomie klucza API, użytkownika lub modelu z wykorzystaniem Redis.
* **Automatyczny Health Check:** Ciągłe monitorowanie dostępności lokalnych workerów GPU i automatyczne wykluczanie niedostępnych silników z puli.
* **Kaskadowy Fallback:** Jeśli lokalny model zgłosi błąd braku pamięci (OOM) lub przekroczy timeout, zapytanie jest natychmiast powtarzane na węźle zapasowym.

### 5. Obserwowalność i audytowalność
* **Metryki Prometheusa:** Gotowe liczniki przepustowości tokenów (tokens/s), czasu do pierwszego tokena (TTFT), opóźnienia generacji oraz kosztów zapytań.
* **Szyfrowane logi audytowe:** Opcjonalny zapis pełnego śladu zapytań szyfrowany kluczem GPG na potrzeby audytów bezpieczeństwa i zgodności z regulacjami.

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
   │  │ ├─ Auth & Rate Limiting (Redis)                  │  │
   │  │ ├─ PII Masker (PESEL, karty, dane osobowe)       │  │
   │  │ └─ Guardrails (Prompt Injection & Secrets)       │  │
   │  └────────────────────────┬─────────────────────────┘  │
   │                           ▼                            │
   │  ┌──────────────────────────────────────────────────┐  │
   │  │ Routing Engine & Load Balancer                   │  │
   │  │ (Priority Failover · Least Conn · Redis Leasing) │  │
   │  └────────────┬────────────────────────┬────────────┘  │
   └───────────────┼────────────────────────┼───────────────┘
                   ▼                        ▼
       [ Silniki lokalne GPU ]    [ Dostawcy chmurowi ]
       ├─ vLLM                    ├─ OpenAI (GPT-4o)
       ├─ Ollama (pLLama)         ├─ Anthropic (Claude)
       └─ LM Studio / llama.cpp   └─ Groq / Mistral
```

---

## Szybki start

LLM Router można uruchomić jako pojedynczy kontener Docker lub wdrożyć w klastrze Kubernetes za pomocą oficjalnego wykresu Helm.

### Uruchomienie w Dockerze

```bash
docker run -d \
  --name llm-router \
  -p 8000:8000 \
  -v $(pwd)/config.yaml:/app/config.yaml \
  radlab/llm-router:latest
```

### Przykładowe zapytanie w Pythonie

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="your-router-key",
)

response = client.chat.completions.create(
    model="pllama-8b",
    messages=[
        {"role": "system", "content": "Jesteś pomocnym asystentem technicznym."},
        {"role": "user", "content": "Jak zoptymalizować wnioskowanie modeli LLM na GPU?"}
    ],
    stream=True,
)

for chunk in response:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

---

## Zasoby i dokumentacja

* **Oficjalna strona projektu:** [llm-router.cloud](https://llm-router.cloud)
* **Repozytorium GitHub:** [radlab-dev-group/llm-router](https://github.com/radlab-dev-group/llm-router)
* **Ekosystem wtyczek:** [radlab-dev-group/llm-router-plugins](https://github.com/radlab-dev-group/llm-router-plugins)
* **Licencja:** Apache 2.0 (dozwolone zastosowania komercyjne i niekomercyjne)
