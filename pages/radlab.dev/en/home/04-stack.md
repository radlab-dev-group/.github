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
    text: "We develop models for Polish: generative models, semantic encoders, extractive QA models, and NER classifiers. We use PyTorch and the Hugging Face ecosystem, and explore what small models can achieve in local experiments."
    tags: ["PyTorch", "Transformers", "Hugging Face", "NLP"]
  - title: "Inference & LLM routing"
    icon: "router"
    text: "We connect local engines and cloud APIs through an OpenAI-compatible interface and an Anthropic endpoint. Configurable plugins, routing, and load-balancing strategies manage traffic, while Redis supports provider coordination and rate limiting."
    tags: ["vLLM", "Ollama", "llama.cpp", "LM Studio", "Redis"]
  - title: "Search & information analysis"
    icon: "data"
    text: "Our semantic search uses Milvus and text embeddings. To discover topics, we combine Sentence-Transformers, t-SNE or UMAP dimensionality reduction, and HDBSCAN clustering. Generative models name topics and produce summaries with sources."
    tags: ["Milvus", "Sentence-Transformers", "HDBSCAN", "t-SNE / UMAP"]
  - title: "Anonymisation & data protection"
    icon: "shield"
    text: "We combine rules and checksum validation with NER models for Polish. Data masking and guardrails can be enabled before a model call. ONNX and INT8 quantisation also allow the anonymisation model to run on CPU."
    tags: ["NER", "RoBERTa", "ONNX / INT8", "PII Masking", "Guardrails"]
---
