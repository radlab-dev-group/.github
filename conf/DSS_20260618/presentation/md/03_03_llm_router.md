# Instalacja i konfiguracja llm-routera

Powrót do [agendy](00_agenda.md).

---

## Czym jest LLM Router?

[LLM Router](https://llm-router.cloud/) to **open-source AI Gateway** 
(w całości na [Apache 2.0](https://github.com/radlab-dev-group/llm-router)) 
dodający warstwę pośredniczącą między aplikacją a dostawcą LLM.
W czasie rzeczywistym kontroluje ruch, dystrybuuje obciążenie względem providerów konkretnego modelu
oraz umożliwia analizę wchodzących i wychodzących zapytań pod kątem bezpieczeństwa (maskowanie, anonimizacja, treści
zabronione).

---

## Ekosystem LLM Router

Projekt podzielony jest na **5 repozytoriów**:

| Repozytorium                                                                       | Opis                                                                                                                                           |
|------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------|
| **[llm-router](https://github.com/radlab-dev-group/llm-router)**                   | Główne repo — REST proxy, Python SDK i zarządzanie konfiguracją                                                                                |
| **[llm-router-api](https://github.com/radlab-dev-group/llm-router)**               | REST proxy route-ujący do backendów LLM (OpenAI-compatible, Ollama, vLLM, LM Studio, Anthropic) z load balancingiem, health checks i streaming |
| **[llm-router-lib](https://github.com/radlab-dev-group/llm-router)**               | Python SDK — typowane requesty i response, automatyczne retry                                                                                  |
| **[llm-router-web](https://github.com/radlab-dev-group/llm-router-web)**           | Flask UI: Config Manager (modele/użytkownicy - UI do zarządzania) + Anonymizer UI (maskowanie danych)                                          |
| **[llm-router-plugins](https://github.com/radlab-dev-group/llm-router-plugins)**   | Pluginy: anonimizatory (maskers), guardrails, routing semantyczny, RAG                                                                         |
| **[llm-router-services](https://github.com/radlab-dev-group/llm-router-services)** | Serwisy uruchamiane w sieci: Sojka/NASK-PIB guardrails, PII masker (token-classification)                                                      |
| **[llm-router-utils](https://github.com/radlab-dev-group/llm-router-utils)**       | Narzędzia CLI: batchowe tłumaczenie, klasyfikacja GenAI, `genai-classifier`, `genai-data-augmentation`                                         |

---

## Architektura — przepływ danych

```
Request → MaskerPipeline → GuardrailPipeline → UtilsPipeline → Model Provider
```

### Masker Plugins (anonimizacja PII)

| Plugin ID     | Typ           | Opis                                                                                                                       |
|---------------|---------------|----------------------------------------------------------------------------------------------------------------------------|
| `fast_masker` | Local         | Bazujące na regexpach PII masker z 30+ typami (email, IP, URL, PESEL, NIP, KRS, REGON, karty kredytowe, JWT, paszporty...) |
| `pii_masker`  | HTTP (remote) | PII masker - klasyfikator w architekturze transformers (token-classification) z cache w pamięci                            |

### Guardrail Plugins (safety check)

| Plugin ID     | Typ           | Opis                                                                   |
|---------------|---------------|------------------------------------------------------------------------|
| `nask_guard`  | HTTP (remote) | Sprawdzanie treści zabronionych modelem HerBERT-PL-Guard (NASK-PIB)    |
| `sojka_guard` | HTTP (remote) | Sprawdzanie treści zabronionych modelem Bielik-Guard-0.1B (SpeakLeash) |

### Utility Plugins

| Plugin ID                    | Typ   | Opis                                                           |
|------------------------------|-------|----------------------------------------------------------------|
| `langchain_rag`              | Local | Retrieval-Augmented Generation z FAISS - baza wiedzy "w locie" |
| `simple_semantic_routing`    | Local | Heurystyczny routing między modelami (intent + complexity)     |
| `semantic_biencoder_routing` | Local | Semantyczny routing między modelami (cosine similarity)        |

### Konfiguracja pipeline-ów

```bash
# Masker pipeline
export LLM_ROUTER_MASKING_STRATEGY_PIPELINE="fast_masker,pii_masker"
export LLM_ROUTER_FORCE_MASKING=1

# Guardrail
export LLM_ROUTER_FORCE_GUARDRAIL_REQUEST=1

# Audit log
export LLM_ROUTER_MASKING_WITH_AUDIT=1
```

---

## Instlacja

### 1. llm-router (core + API)

```bash
# Z repozytorium źródłowego:
git clone https://github.com/radlab-dev-group/llm-router.git
cd llm-router
pip install -e .

# Lub przez Docker:
bash run-docker.sh

# Lub przez skrypt startowy:
bash run-rest-api-gunicorn.sh
```

Po uruchomieniu REST API jest dostępne pod `http://localhost:8080` (lub wskazanym portem).

### 2. llm-router-services (guardrails + masker)

```bash
git clone https://github.com/radlab-dev-group/llm-router-services.git
cd llm-router-services
pip install -e .

# Ustaw environment variables:
export LLM_ROUTER_API_HOST=0.0.0.0
export LLM_ROUTER_API_PORT=5000
export LLM_ROUTER_NASK_PIB_GUARD_ENABLED=1
export LLM_ROUTER_SOJKA_GUARD_ENABLED=1

# Uruchomienie (zalecane):
./run_servcices.sh
```

### 3. llm-router-utils (CLI tools)

```bash
git clone https://github.com/radlab-dev-group/llm-router-utils.git
cd llm-router-utils
pip install -e .
pip install ".[llm-router]"   # llm-router + llm-router-services z git

# Dodatkowe zależności (klasyfikator):
pip install rdl-ml-utils datasets pandas openpyxl
```

---

## Użycie ze skryptami tutorialu

Po uruchomieniu llm-router pod `http://localhost:8080`, skrypty korzystają z niego jako z jednolitego endpoint-u:

```bash
# Labelowanie (genai-classifier z llm-router-utils)
genai-classifier \
  --dataset-dir="resources/dataset/twitteremo/" \
  --prompts-dir=resources/prompts/classifier \
  --output-dir=resources/dataset/twitteremo/genailabelled \
  --llm-router-url="http://localhost:8080" \
  --model-name="gpt-oss:120b" \
  --temperature=0.0 \
  --batch-save-size=2 \
  --num-workers=2 \
  --n-sample=0 \
  --text-column-name="tekst"

# Augmentacja (genai-data-augmentation z llm-router-utils)
genai-data-augmentation \
  --dataset-path="resources/dataset/twitteremo/..._labels.jsonl" \
  --labels="pozytywny" \
  --output-dir="resources/dataset/twitteremo/augmented" \
  --llm-router-url="http://localhost:8080" \
  --model-name="gpt-oss:120b" \
  --n-sample=350
```

---

## Rozwiązywanie problemów

| Problem                      | Rozwiązanie                                                                         |
|------------------------------|-------------------------------------------------------------------------------------|
| `Connection refused`         | Sprawdź czy REST API (llm-router) i/lub llm-router-services działają                |
| Model się nie ładuje         | Zweryfikuj czy model istnieje na backendzie (`ollama list`, `vllm list`)            |
| Timeout przy dużych modelach | Zwiększ `timeout` w konfiguracji llm-router                                         |
| Brak VRAM                    | Użyj CPU-only vendor (Ollama / llama.cpp) lub zmniejsz rozmiar batcha               |
| PII nie maskowane            | Upewnij się, że `LLM_ROUTER_FORCE_MASKING=1` i masker pipeline jest skonfigurowany  |
| Brak guardrails              | Upewnij się, że `LLM_ROUTER_FORCE_GUARDRAIL_REQUEST=1` i llm-router-services działa |

---

## Kluczowe możliwości LLM Router

| Cecha                               | Opis                                                                               |
|-------------------------------------|------------------------------------------------------------------------------------|
| **Unified REST interface**          | Jeden endpoint dla OpenAI-compatible, Ollama, vLLM, LM Studio, Anthropic           |
| **Provider-agnostic streaming**     | Chunked responses z proper Cache-Control/Pragma headers                            |
| **Dynamic model configuration**     | JSON (`models-config.json`) — dostawcy, nazwa modelu, per-model konfiguracja       |
| **Load balancing**                  | Dystrybucja ruchu względem providerów z licznikiem wykorzsytania (różne strategie) |
| **Health & metadata**               | `/ping` (200 OK), `/tags` (model metadata), `/metrics` (Prometheus)                |
| **Request validation**              | Pydantic models — obsługa błędów                                                   |
| **Structured logging**              | Log level, pliki, formatowanie JSON                                                |
| **Multi-provider model support**    | Każdy model może mieć wielu różnych providerów (VLLM, Ollama, OpenAI, Anthropic)   |
| **Embeddings support**              | Dedykowane endpointy dla embeddingów dla większości providerów                     |
| **Docker & Kubernetes ready**       | Dockerfile + Helm charts                                                           |
| **Extensible conversation formats** | Chat, system prompt, extended conversation                                         |

---

Powrót do [agendy](00_agenda.md).
