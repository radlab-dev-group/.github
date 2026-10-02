---
title: "RDL Playground AI"
subtitle: "Interactive research sandbox and experimentation platform for Polish NLP models"
slug: "playground"
description: "RDL Playground AI is an open research and demonstration platform by RadLab. It allows direct interaction with Polish-tailored pLLama models, sentiment classifiers, live news streaming analysis, and conversational AI agents in real-world NLP scenarios."
icon: "flask"
status: "Research Platform · Non-Profit"
version: "Live Web App"
tags: ["Playground AI", "pLLama Models", "Public Chat", "Polarity 3C", "News Stream", "NLP Research"]
actions:
  - {label: "Launch Playground (playground.radlab.dev)", href: "https://playground.radlab.dev", style: primary}
  - {label: "Models on Hugging Face", href: "https://huggingface.co/radlab", style: quiet}
  - {label: "Research blog & papers", href: "/en/blog/", style: quiet}
---

## What is RDL Playground AI?

**RDL Playground AI** is an interactive experimentation environment built by the RadLab team to test, evaluate, and showcase open language models, token classifiers, and intelligent agents developed for Polish and multilingual NLP.

It bridges the gap between machine learning research (R&D) and production reality. Engineers, analysts, and researchers can freely experiment with models, examining how they handle complex inflection, contextual nuance, and dense information streams.

---

## Core Modules & Experiments

```text
┌─────────────────────────────────────────────────────────────────┐
│                       RDL PLAYGROUND AI                         │
├────────────────────┬────────────────────┬───────────────────────┤
│  Public Chat       │ Live News Stream   │ Information Browser & │
│  & AI Agents       │ & 3C Sentiment     │ Knowledge Explorer    │
│  ├─ pLLama 1B-70B  │ ├─ Live Ingestion  │ ├─ Topic Clustering   │
│  └─ Supervisor     │ └─ Polarity Scoring│ └─ Entity Graphs      │
└────────────────────┴────────────────────┴───────────────────────┘
```

### 1. Public Chat & Specialized AI Agents
* **pLLama Model Serving:** Chat directly with models tuned for Polish (ranging from lightweight 1B/3B edge models to capable 8B and 70B checkpoints).
* **Content Supervisor Agent:** Built-in verification agents that monitor factual accuracy, detect hallucinations, and evaluate grounded responses.
* **Session Sharing (Chat Hashes):** Share reproducible conversation states via cryptographic hash identifiers.

### 2. Live News Stream & Polarity Classification (3C)
* **Real-Time Web Feed:** Continuous ingestion from major Polish news portals and international sources.
* **3-Class Polarity Scoring:** Incoming articles are scored in real time by the `radlab/polarity-3c` RoBERTa model:
  * **Positive:** Constructive, progress-oriented, or optimistic reports.
  * **Negative:** News involving crises, conflicts, or systemic issues.
  * **Ambivalent / Neutral:** Fact-centric reporting or balanced emotional perspectives.

### 3. Information Browser & Knowledge Explorer
* **Emergent Topic Discovery:** Groups thousands of articles into coherent daily clusters without rigid manual taxonomies.
* **Information Relationship Graphs:** Maps connections between events, entities, and sources over time.
* **Source Propagation Analysis:** Traces which publications initiated specific coverage and how stories propagated across the digital ecosystem.

### 4. Public Metrics & Observatory
* Clear visual dashboards tracking daily emotional distributions in media, article ingestion volume, and model inference benchmarks.

---

## Technical Infrastructure

The Playground is powered by RadLab’s internal stack:
* **Gateway Layer:** Inbound traffic is handled by **LLM Router**, managing queues, worker balancing, and token streaming.
* **GPU Inference:** High-throughput serving via **vLLM** and optimized precision quantizations.
* **Open Weights:** Model checkpoints running on the Playground are released open-source on our Hugging Face organisation.

---

## Open Access

RDL Playground AI is completely free for researchers, developers, and students:
* No accounts or credentials required,
* No advertising, paywalls, or data monetization,
* Live at: **[playground.radlab.dev](https://playground.radlab.dev)**
