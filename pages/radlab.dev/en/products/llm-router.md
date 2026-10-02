---
title: "LLM Router"
subtitle: "Open-source AI gateway for routing requests across language models"
slug: "llm-router"
description: "LLM Router is an AI gateway you run in your own infrastructure. It offers an OpenAI-compatible interface and an Anthropic endpoint for local engines and external APIs, with configurable plugins, data protection, and load balancing."
icon: "router"
status: "Open Source · Apache-2.0"
version: "v0.2.3"
tags: ["AI Gateway", "vLLM", "Ollama", "PII Masking", "Load Balancing", "Guardrails", "Self-Hosted"]
actions:
  - {label: "Official website (llm-router.cloud)", href: "https://llm-router.cloud", style: primary}
  - {label: "GitHub (radlab-dev-group)", href: "https://github.com/radlab-dev-group/llm-router", style: quiet}
  - {label: "Technical documentation", href: "https://llm-router.cloud/docs/0.2.3/overview.html", style: quiet}
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
