---
order: 4
layout: stack
anchor: stack
eyebrow: "Tech stack"
title: "The technology foundation behind our systems"
intro: "We engineer our proprietary models, routers, and AI platforms on a proven, high-performance open-source ecosystem optimized for data privacy, low inference latency, and production reliability."
pills:
  - {name: "PyTorch", role: "model training & fine-tuning"}
  - {name: "Hugging Face", role: "NLP ecosystem & tokenizers"}
  - {name: "vLLM", role: "inference engine & PagedAttention"}
  - {name: "Ollama", role: "local model serving"}
  - {name: "Milvus", role: "vector database & semantic search"}
  - {name: "FastAPI", role: "async microservices"}
  - {name: "Docker", role: "environment containerization"}
  - {name: "CUDA", role: "GPU hardware acceleration"}
cards:
  - title: "Models & training"
    icon: "ml"
    text: "We develop the pLLama model family, domain encoders, and extractive QA checkpoints. We use PyTorch, Transformers, FlashAttention, and parameter-efficient fine-tuning (PEFT/LoRA) on curated Polish corpora."
    tags: ["PyTorch", "Transformers", "PEFT / LoRA", "FlashAttention", "Hugging Face"]
  - title: "Inference & LLM routing"
    icon: "router"
    text: "We optimize latency and token throughput across generative workloads. We integrate vLLM, Ollama, llama.cpp, and TensorRT-LLM for sub-second token streaming, dynamic failover, and a unified API interface."
    tags: ["vLLM", "Ollama", "llama.cpp", "TensorRT-LLM", "Streaming API"]
  - title: "Vectors & semantic search"
    icon: "data"
    text: "High-throughput semantic search and production RAG pipelines are powered by the Milvus vector database. We process, cluster, and index multi-gigabyte corpora using FAISS and Polars."
    tags: ["Milvus", "FAISS", "Polars", "Semantic Search", "RAG"]
  - title: "Systems & production"
    icon: "code"
    text: "We turn machine learning research into reliable on-premise and private cloud software. We build asynchronous microservices with FastAPI and Python, ensuring data sovereignty, container isolation, and GPU acceleration."
    tags: ["Python", "FastAPI", "Docker", "CUDA", "On-Premise / Private Cloud"]
---
