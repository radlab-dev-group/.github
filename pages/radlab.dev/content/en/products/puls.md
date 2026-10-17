---
title: "Puls Informacji"
subtitle: "News from multiple sources brought together in one article on your chosen topic"
slug: "puls"
description: "Puls Informacji is a RadLab web app that creates articles in response to questions about current events. It searches RadLab's own index of news from multiple outlets, includes source links, and shows sentiment analysis of the search results."
icon: "spark"
status: "Web App · Demo"
version: "Next.js 15 · RAG"
tags: ["RAG", "Generative AI", "Information Synthesis", "News Search", "Polarity 3C", "Local Index"]
actions:
  - {label: "Launch app (puls.apps.radlab.dev)", href: "https://puls.apps.radlab.dev", style: primary}
  - {label: "Read about RAG on the blog", href: "/en/2025-12-27/can-a-knowledge-base-be-easily-introduced-for-genai/", style: quiet}
---

## What is Puls Informacji?

**Puls Informacji** (`puls.apps.radlab.dev`) is a RadLab web app that brings the **News Creator** features from RDL Playground AI to a dedicated interface. It gathers news from multiple outlets and uses it to create an article on your chosen topic, reducing the need to browse news sites individually.

Enter a question or choose a suggested topic. Then select a writing style (**plain language or formal**) and a time window (**the past day, 2 days, or 7 days**). The system searches the index, gathers relevant reports, and produces a coherent article with source links.

---

## How It Works (RAG)

Puls Informacji uses **Retrieval-Augmented Generation (RAG)**:

```text
[ Question ] → [ RadLab Index Search ] → [ Selected News ]
                                                ↓
[ Article + Sources + Stats ] ← [ AI Text Generation ]
```

1. **RadLab's Own News Index:** The app searches an index of websites analyzed by RadLab, without external search APIs. According to the app, news from the News Stream is indexed after approximately 10 minutes.
2. **Source-Based Generation:** The model writes an article using the retrieved news. This reduces the risk of fabricated information but does not eliminate errors — important facts should be checked against the linked sources.
3. **Sentiment Analysis (Polarity 3C):** A chart shows the proportions of positive, negative, and ambivalent news items in the search results.
4. **Sources and Statistics:** The article is accompanied by source links, model and generation-time details, the number of matched news items, a word count, and an estimated reading time.

---

## Technology and Features

The interface adapts to desktop and mobile screens:

* **Next.js 15 (App Router), React 19, and TypeScript:** The interface uses Tailwind CSS v4 and CSS/SVG charts, with no additional charting library or UI kit.
* **Server-Side Proxy:** Next.js API routes forward requests to RadLab services, so the browser does not connect directly to the backend server.
* **Two Interface Languages:** Polish and English.
* **Copy and Export:** Copy the generated text to the clipboard or download it as a Markdown (`.md`) file.

---

## Access & Links

* **Open the App:** [puls.apps.radlab.dev](https://puls.apps.radlab.dev).
* **Status:** Demo within the RadLab ecosystem.
