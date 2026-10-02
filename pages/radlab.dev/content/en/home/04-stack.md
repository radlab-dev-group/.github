---
order: 4
layout: stack
anchor: stack
eyebrow: "Tech stack"
title: "The technology foundation behind our systems"
intro: "We combine language models, semantic search, and data protection tools. This stack supports our own solutions — from local news analysis to managing traffic between models."
pills:
  - {name: "PyTorch", role: "model training & fine-tuning"}
  - {name: "Transformers", role: "language models & classifiers"}
  - {name: "Sentence-Transformers", role: "text embeddings"}
  - {name: "vLLM", role: "language model inference"}
  - {name: "Ollama", role: "local model serving"}
  - {name: "Milvus", role: "vector database & semantic search"}
  - {name: "Redis", role: "traffic coordination & rate limiting"}
  - {name: "ONNX", role: "NER model inference on CPU"}
cards:
  - title: "Models & training"
    icon: "ml"
    href: "products/playground"
    text: "We develop dedicated models for Polish: generative pLLama models, semantic encoders, extractive QA, and NER classifiers. Built with PyTorch and the Hugging Face ecosystem, optimized for high throughput on local hardware (RDL Playground AI)."
    tags: ["PyTorch", "Transformers", "Hugging Face", "pLLama / QA"]
  - title: "Inference & LLM routing"
    icon: "router"
    href: "products/llm-router"
    text: "The foundation of LLM Router: connecting local inference engines (vLLM, Ollama) with cloud APIs via OpenAI/Anthropic endpoints. Features configurable plugin pipelines, advanced load-balancing strategies, and Redis coordination for self-hosted sovereignty."
    tags: ["LLM Router", "vLLM", "Ollama", "Redis", "Load Balancing"]
  - title: "Search & information analysis"
    icon: "data"
    href: "products/radar"
    text: "The analytical core of Radar Informacji: semantic search via Milvus, dense text embeddings, non-linear dimensionality reduction (t-SNE/UMAP), and dynamic HDBSCAN clustering for uncategorized trend discovery in news streams."
    tags: ["Radar Informacji", "Milvus", "HDBSCAN", "Sentence-Transformers"]
  - title: "Anonymisation & data protection"
    icon: "shield"
    href: "products/pii-masker"
    text: "The engine behind PII Masker: dual-layer privacy protection (deterministic FastMasker with checksum validation + RoBERTa NER). ONNX INT8 quantization enables masking on CPU, supporting data minimization in projects subject to GDPR and the EU AI Act."
    tags: ["PII Masker", "FastMasker", "RoBERTa NER", "ONNX INT8", "RODO / GDPR"]
---
