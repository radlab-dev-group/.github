---
title: "LLM Router"
subtitle: "Open-source AI gateway for routing requests across language models"
slug: "llm-router"
description: "LLM Router is an AI gateway you run in your own infrastructure. It offers an OpenAI-compatible interface and an Anthropic endpoint for local engines and external APIs, with configurable plugins, data protection, and load balancing."
icon: "router"
status: "Open Source · Apache-2.0"
version: "v1.1.6"
tags: ["AI Gateway", "vLLM", "Ollama", "PII Masking", "Load Balancing", "Guardrails", "Self-Hosted"]
actions:
  - {label: "Official website (llm-router.cloud)", href: "https://llm-router.cloud", style: primary}
  - {label: "GitHub (radlab-dev-group)", href: "https://github.com/radlab-dev-group/llm-router", style: quiet}
  - {label: "Technical documentation", href: "https://llm-router.cloud/docs/", style: quiet}
---

## What is LLM Router?

**LLM Router** is an open-source AI gateway running in your own infrastructure — on local servers, in private clouds, or in air-gapped environments. It sits between your applications and the model providers you configure.

Applications use one **OpenAI-compatible API** or the native **Anthropic `/v1/messages`** endpoint. The gateway forwards requests to local engines such as **vLLM**, **Ollama**, **llama.cpp**, and **LM Studio**, or to configured external APIs. Along the way, it can apply authentication, data masking, guardrails, and routing rules. Pipeline stages are enabled through configuration.

---

## Key Capabilities

### 1. One Interface for Models
The gateway supports endpoints including `/v1/chat/completions`, `/v1/responses`, and `/v1/embeddings`, as well as `/v1/messages` for Anthropic clients. Responses can stream via SSE. Models, providers, and gateway behaviour are set in a configuration file and environment variables.

### 2. Configurable Plugin Pipeline
Plugins let you enable and arrange request-processing stages without changing application code:

* **PII masking:** `fast_masker` applies rules for identifiers and contact details; `pii_masker` can also use an ML classifier.
* **Guardrails:** `nask_guard` and `sojka_guard` check requests before the model is called.
* **Semantic routing:** With `model: "auto"`, an optional plugin can select a model based on the request content.
* **Extensions:** Add your own plugins, including knowledge-base context enrichment.

### 3. Load Balancing Strategies
A strategy chooses a **provider for the requested model** when more than one provider serves it:

1. **`balanced` (default):** Selects the provider used least often for that model.
2. **`weighted`:** Distributes requests according to configured, static provider weights.
3. **`dynamic_weighted` (beta):** Adjusts weights using observed latency.
4. **`first_available`:** Grants exclusive use of the first available provider; requires Redis for coordination between workers.
5. **`first_available_optim`:** Prefers hosts that have already loaded the model to avoid repeated loading; uses Redis.
6. **`first_available_optim_nworkers`:** Allows up to `nworkers` concurrent requests per provider and selects the provider with the fewest occupied slots; Redis coordinates the leases.

See the [load balancing strategy documentation](https://github.com/radlab-dev-group/llm-router/blob/main/llm_router_api/docs/LB_STRATEGIES.md) for full behaviour and requirements.

### 4. Availability & Traffic Control
* **Provider errors:** The gateway tries other providers **of the same model** first. Only when that model cannot serve the request can a separately configured `fallback_model` take over. This is not a balancing strategy or an automatic switch to a cloud model.
* **Keys and limits:** Authentication uses keys with endpoint permissions; Redis-backed sliding-window request limits are applied per key and client IP.

### 5. Observability & Auditing
* **Prometheus:** When enabled, `/metrics` exposes provider call, error, retry, and token counters as well as latency histograms.
* **GPG audit logs:** Masking and guardrail decisions can be stored as encrypted entries.

---

## Quickstart

LLM Router runs as a Docker container and connects to OpenAI clients through a changed `base_url`. Support for individual API features also depends on the selected model provider.

### 1. Run via Docker

This example assumes a vLLM server running on the host on port `8000`, serving a model named `llama-3.1-8b`. The router does not start the model for you. Save this as `config.json`:

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

The `rc1` tag and variables follow the [repository's Docker instructions](https://github.com/radlab-dev-group/llm-router#-docker). The model must be reachable from the container; on Linux a backend bound only to `127.0.0.1` is not sufficient. This gateway example is localhost-only; before exposing it on a network, enable authentication and TLS as described in the [authentication documentation](https://github.com/radlab-dev-group/llm-router/blob/main/llm_router_api/docs/AUTHENTICATION.md).

### 2. Python Client (OpenAI SDK)

```python
from openai import OpenAI

# Direct your requests to LLM Router gateway
client = OpenAI(
    base_url="http://localhost:5555/v1",
    api_key="your-api-key"  # or any string if auth is disabled
)

response = client.chat.completions.create(
    model="llama-3.1-8b",
    messages=[
        {"role": "system", "content": "You are a helpful software engineering assistant."},
        {"role": "user", "content": "How do I configure resilient LLM routing?"}
    ],
    temperature=0.7,
    stream=True
)

for chunk in response:
    if chunk.choices and chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

### 3. cURL Example

```bash
curl http://localhost:5555/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "model": "llama-3.1-8b",
    "messages": [
      {"role": "user", "content": "Hello! Explain the gateway architecture briefly."}
    ]
  }'
```

---

## Comparison with Alternatives (Differentiators)

| Feature / Capability | LLM Router | LiteLLM | Ollama (standalone) | Portkey / Cloud Gateways |
| :--- | :--- | :--- | :--- | :--- |
| **Deployment Model** | Self-hosted; air-gapped with local models and dependencies | Self-hosted / managed services | Local model server | Open self-hosted gateway / SaaS platform |
| **PII Masking & Guardrails** | Configurable Polish plugins: FastMasker, RoBERTa NER, NASK Guard, Sójka Guard | Guardrail integrations including Presidio; scope depends on integration and edition | Requires an additional application layer | Guardrail integrations; scope depends on deployment and plan |
| **Routing & Load Balancing** | 6 strategies including weights, worker slots, and Redis coordination | Random/weighted, latency-based, usage-based, and least-busy strategies | Serves its own models, not a multi-provider gateway | Load balancing, fallbacks, and conditional routing |
| **API Protocol Support** | OpenAI-compatible + Anthropic `/v1/messages` | Unified OpenAI-compatible API for multiple providers | Ollama API / partial OpenAI compatibility | Unified API for multiple providers |
| **Observability & Audit** | Optional Prometheus `/metrics` and encrypted GPG audit | Metrics, logging, and spend tracking | Server logs | Platform observability features depend on plan |
| **License** | Apache 2.0 | MIT core; enterprise features under separate terms | MIT | MIT open gateway; commercial platform separately |

LLM Router stands out through its Polish plugin ecosystem and control over local infrastructure, not exclusive support for routing or self-hosting. This compares operating models, not performance benchmarks. Sources: [LLM Router](https://github.com/radlab-dev-group/llm-router), [LiteLLM routing](https://docs.litellm.ai/docs/routing), [Portkey gateway](https://github.com/Portkey-AI/gateway), [Ollama API compatibility](https://docs.ollama.com/api/openai-compatibility).

---

## Architecture Overview

```text
[ Client Applications & AI Agents ]
                 │ (OpenAI / Anthropic API format)
                 ▼
   ┌────────────────────────────────────────────────────────┐
   │                     LLM ROUTER                         │
   │                                                        │
   │  ┌──────────────────────────────────────────────────┐  │
   │  │ Pre-inference Pipeline                           │  │
   │  │ ├─ Auth & Rate Limiting (optional)                │  │
   │  │ ├─ PII Masking                                   │  │
   │  │ └─ Guardrails & Semantic Routing                 │  │
   │  └────────────────────────┬─────────────────────────┘  │
   │                           ▼                            │
   │  ┌──────────────────────────────────────────────────┐  │
   │  │ Routing Engine & Load Balancer                   │  │
   │  │ (e.g. balanced · weighted · first_available)     │  │
   │  └────────────┬────────────────────────┬────────────┘  │
   └───────────────┼────────────────────────┼───────────────┘
                   ▼                        ▼
       [ Local Inference Engines ]   [ Cloud Model APIs ]
       ├─ vLLM                       ├─ OpenAI
       ├─ Ollama                     └─ Anthropic
       └─ LM Studio / llama.cpp
```

---

## Resources & Links

* **Official Website:** [llm-router.cloud](https://llm-router.cloud)
* **GitHub Repository:** [radlab-dev-group/llm-router](https://github.com/radlab-dev-group/llm-router)
* **Plugins Ecosystem:** [radlab-dev-group/llm-router-plugins](https://github.com/radlab-dev-group/llm-router-plugins)
* **License:** Apache 2.0 (commercial and non-commercial friendly)
