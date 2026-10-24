---
title: "Semantic Search Engine"
subtitle: "From your own documents to search and AI answers"
slug: "semantic-search-engine"
description: "Semantic Search Engine combines document management, semantic and hybrid search, and RAG answers. A Django REST API backend and a FastAPI interface with Jinja2 help you build and search your own knowledge bases."
icon: "data"
status: "Backend API · Web Interface"
version: "Django · FastAPI · RAG"
tags: ["Semantic Search", "Hybrid Search", "RAG", "Milvus", "PostgreSQL", "Knowledge Base"]
actions:
  - {label: "GitHub — engine & API", href: "https://github.com/radlab-dev-group/semantic-search-engine", style: primary}
  - {label: "GitHub — user interface", href: "https://github.com/radlab-dev-group/semantic-search-engine-ui", style: quiet}
---

## What Is Semantic Search Engine?

**Semantic Search Engine** is a toolkit for building a knowledge base from your own documents. It prepares and indexes content, retrieves passages by the meaning of a question, and generates answers using the retrieved material through **RAG (Retrieval-Augmented Generation)**.

The product has two cooperating parts: an **engine with a REST API** and a **web interface**. Use the ready-made panel or integrate the backend into your own application; the engine repository also includes the `sse_lib` Python client.

---

## What Can You Use It For?

* **Searching documentation and internal material:** Find related passages even when a question uses different wording from the document.
* **Team knowledge bases:** Organize content into collections, browse documents, and decide which ones participate in search.
* **Source-based assistants:** Build answers from retrieved passages rather than relying solely on a model's prior knowledge.
* **Search and RAG experiments:** Choose embedding models, rerankers, filters, and generation settings; revisit query history and collect answer ratings.

---

## Key Features

* **File uploads or pasted text:** The interface accepts PDF, DOCX, TXT, HTML, Markdown, and ZIP archives. Content is prepared for indexing and split into chunks.
* **Chunking controls:** Set chunk size and overlap for a collection. The panel takes the chosen embedding model's length limit into account.
* **Knowledge base management:** Create and delete collections, inspect document content, delete chunks, and include or exclude documents from search results.
* **Indexing progress:** Track processed, pending, and failed documents. The backend can index within the request or optionally through a Celery queue with RabbitMQ.
* **Semantic and hybrid search:** Combine Milvus vector retrieval with PostgreSQL full-text search using RRF (Reciprocal Rank Fusion). An optional reranker reorders results against the question.
* **Filters and models:** Narrow searches by categories and documents, among other criteria, and use configured embedding, reranking, and generative models.
* **RAG answers and feedback:** Browse retrieval results first, followed by the model's answer loaded asynchronously. Rate answers with stars and comments, and revisit saved searches within a collection.
* **Polish and English interface:** Switch languages and choose a light, dark, or automatic theme. Interface assets are served locally, without external CDN dependencies.

---

## Architecture and Technology

```text
Browser → FastAPI + Jinja2 interface → Django REST API
                                          ├─ PostgreSQL: documents, metadata, and text search
                                          ├─ Milvus: vector index
                                          ├─ Embedding models and rerankers
                                          └─ Generative models: RAG answers
```

The **backend** uses Python, Django, and Django REST Framework. PostgreSQL stores relational data, while Milvus provides vector retrieval. Embedding models and rerankers match content to queries; a configured generative model creates an answer from the results.

The **interface** is a separate Python application built with FastAPI and Jinja2 templates, with local CSS and JavaScript. It communicates with the engine through the REST API and supports login using a backend token. It does not require a SPA framework.

The system can run on your own infrastructure. Communication with external services depends on the configured models and integrations: a local interface does not automatically mean all data processing is local. Retrieval relevance and answer quality depend on the documents, chunking, and chosen models; AI answers still require verification.

---

## Code and Documentation

* **Engine, API, and Python client:** [semantic-search-engine](https://github.com/radlab-dev-group/semantic-search-engine).
* **User interface and setup instructions:** [semantic-search-engine-ui](https://github.com/radlab-dev-group/semantic-search-engine-ui).