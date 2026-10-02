---
title: "LLM Router"
subtitle: "High-performance open-source AI gateway & control plane for self-hosted LLM infrastructure"
slug: "llm-router"
description: "LLM Router is a self-hosted AI gateway for on-premise and cloud infrastructure. It exposes a unified OpenAI and Anthropic-compatible API in front of vLLM, Ollama, LM Studio, and cloud providers with PII masking, guardrails, routing, and load balancing."
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

**LLM Router** is a high-throughput, open-source AI gateway and control plane designed to run directly inside your own infrastructure — on bare-metal GPU servers, in private clouds, or within air-gapped enterprise networks.

Your applications and AI agents communicate with a single, dependable API compliant with **OpenAI API** and **Anthropic API** standards. LLM Router manages traffic routing across local engines (**vLLM**, **Ollama**, **LM Studio**) and external cloud providers (**OpenAI**, **Anthropic**, **Groq**, **Mistral**), enforcing security policies, PII anonymization, and cost controls.

---

## Key Capabilities

### 1. Unified API Surface
* **Drop-in compatibility:** Full implementation of `/v1/chat/completions`, `/v1/completions`, `/v1/embeddings`, and `/v1/models`. Swap your endpoint URL without refactoring application logic.
* **Low-latency streaming:** Native Server-Sent Events (SSE) token forwarding with sub-2ms gateway overhead.
* **Structured generation:** Support for JSON Schema, grammar enforcement, and tool/function calling across local and cloud backends.

### 2. Deterministic Plugin Pipeline
LLM Router processes every incoming request through an extensible hook pipeline before inference (*pre-inference*) and after generation (*post-inference*):

* **Multi-tier PII Protection:** Automatic detection and masking of sensitive identifiers (national IDs, tax IDs, credit cards, emails, phone numbers) before data leaves your boundary.
* **Content Guardrails:** Prompt injection detection, disallowed topic filtering, and token/secret leakage prevention.
* **Dynamic RAG Enrichment:** Just-in-time prompt enrichment with documents from vector databases or internal knowledge bases.

### 3. 6 Advanced Load Balancing Strategies
* **Round Robin:** Equal distribution across healthy instances.
* **Least Connections:** Routes queries to the worker with the lowest active request count.
* **Latency-Aware:** Dynamic EMA-based routing prioritizing the lowest TTFT (time to first token).
* **Priority Failover:** Directs traffic to local GPU engines by default and fails over to cloud models only under heavy load or failure.
* **Random Balancing:** Weighted stochastic traffic distribution.
* **Distributed Redis Leasing:** Multi-instance concurrency control and lease-based scheduling.

### 4. Reliability & Traffic Management
* **Distributed Rate Limiting:** Enforce requests-per-minute (RPM) and tokens-per-minute (TPM) limits per API key, tenant, or model via Redis.
* **Health Checks & Circuit Breaking:** Automated GPU worker probing with automatic removal of failing endpoints.
* **Cascading Fallbacks:** Seamless retry on alternate workers if an out-of-memory (OOM) or timeout error occurs.

### 5. Observability & Auditing
* **Prometheus Metrics:** Out-of-the-box telemetry for token throughput (tokens/sec), TTFT, error rates, and cost estimation.
* **GPG-Encrypted Audit Logs:** Tamper-evident logging of prompts and completions for compliance and enterprise security audits.

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
   │  │ ├─ Auth & Rate Limiting (Redis)                  │  │
   │  │ ├─ PII Masker (Sensitive & Personal Data)        │  │
   │  │ └─ Guardrails (Prompt Injection & Secrets)       │  │
   │  └────────────────────────┬─────────────────────────┘  │
   │                           ▼                            │
   │  ┌──────────────────────────────────────────────────┐  │
   │  │ Routing Engine & Load Balancer                   │  │
   │  │ (Priority Failover · Least Conn · Redis Leasing) │  │
   │  └────────────┬────────────────────────┬────────────┘  │
   └───────────────┼────────────────────────┼───────────────┘
                   ▼                        ▼
       [ Local Inference Engines ]   [ Cloud Model APIs ]
       ├─ vLLM                       ├─ OpenAI (GPT-4o)
       ├─ Ollama (pLLama)            ├─ Anthropic (Claude)
       └─ LM Studio / llama.cpp      └─ Groq / Mistral
```

---

## Quickstart

Run LLM Router via Docker or deploy to Kubernetes using the official Helm chart.

### Docker Run

```bash
docker run -d \
  --name llm-router \
  -p 8000:8000 \
  -v $(pwd)/config.yaml:/app/config.yaml \
  radlab/llm-router:latest
```

### Python SDK Example

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="your-router-key",
)

response = client.chat.completions.create(
    model="pllama-8b",
    messages=[
        {"role": "system", "content": "You are a helpful technical assistant."},
        {"role": "user", "content": "How do you optimize LLM inference on modern GPUs?"}
    ],
    stream=True,
)

for chunk in response:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

---

## Resources & Links

* **Official Website:** [llm-router.cloud](https://llm-router.cloud)
* **GitHub Repository:** [radlab-dev-group/llm-router](https://github.com/radlab-dev-group/llm-router)
* **Plugins Ecosystem:** [radlab-dev-group/llm-router-plugins](https://github.com/radlab-dev-group/llm-router-plugins)
* **License:** Apache 2.0 (commercial and non-commercial friendly)
