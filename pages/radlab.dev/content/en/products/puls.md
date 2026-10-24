---
title: "Puls Informacji"
subtitle: "News from multiple sources brought together in one article on your chosen topic"
slug: "puls"
description: "Puls Informacji is a RadLab web app that creates articles in response to questions about current events. It searches RadLab's own index of news from multiple outlets, includes source links, and shows sentiment analysis of the search results."
icon: "spark"
status: "Web App · Demo"
version: "Flask · RAG"
tags: ["RAG", "Generative AI", "Information Synthesis", "News Search", "Polarity 3C", "Local Index"]
actions:
  - {label: "Launch app (puls.apps.radlab.dev)", href: "https://puls.apps.radlab.dev", style: primary}
  - {label: "Read about RAG on the blog", href: "/en/2025-12-27/can-a-knowledge-base-be-easily-introduced-for-genai/", style: quiet}
---

## What is Puls Informacji?

**Puls Informacji** (`puls.apps.radlab.dev`) is a RadLab web app that brings the **News Creator** features from RDL Playground AI to a dedicated interface. It gathers news from multiple outlets and uses it to create an article on your chosen topic, reducing the need to browse news sites individually.

Enter a question or choose a suggested topic. Then select a writing style (**plain language or formal**) and a time window (**the past day, 2 days, or 7 days**). The system searches the index, gathers relevant reports, and produces a coherent article with source links.

---

## What Can You Use Puls For?

* **A daily news briefing:** Bring reports on a topic you care about into one article rather than opening news sites one by one.
* **Background before a meeting or further reading:** Get an introduction to current developments in an industry, technology, or public affairs, then follow the links to the original material.
* **A look back over recent days:** Choose a 1-, 2-, or 7-day window to gather the latest reports or explore a broader context.
* **Material for your own notes:** Choose plain language or a formal tone, then copy the result or save it as Markdown as a starting point for further work.

Puls does not replace editorial fact-checking or a comprehensive web search. Its answers depend on the news available in the index and how well it matches your question.

---

## Architecture and How It Works (RAG)

The application uses **Python and Flask** to render the interface from **Jinja2 templates** and communicate with the **RadLab backend**. Static JavaScript handles browser interactions, while search and generation run in RadLab services. It uses **Retrieval-Augmented Generation (RAG)**: the model receives news retrieved for the specific query.

```text
Browser → Flask application API → RadLab backend
                               ├─ Categories and available news sites
                               ├─ News index search
                               └─ Article generation from matched news
Browser ← Article, source material, and metadata
```

1. **RadLab's Own News Index:** The app searches an index of websites analyzed by RadLab, without external search APIs. According to the app, news from the News Stream is indexed after approximately 10 minutes.
2. **Source-Based Generation:** The model writes an article using the retrieved news. This reduces the risk of fabricated information but does not eliminate errors — important facts should be checked against the linked sources.
3. **Sentiment Analysis (Polarity 3C):** A chart shows the proportions of positive, negative, and ambivalent news items in the search results.
4. **Sources and Statistics:** The article is accompanied by source links, model and generation-time details, the number of matched news items, a word count, and an estimated reading time.

On page load, the interface fetches the categories and available sites, all of which are included in the search. It then sends the question and selected time window to the search service. The matched news IDs are passed to a separate generation request alongside the question and writing-style instruction. If no material is found, the app displays a notice instead of starting generation.

---

## Technology and Features

The interface adapts to desktop and mobile screens:

* **Python, Flask, and Jinja2:** The server renders interface templates, while local CSS and JavaScript files handle styling and interactions. The application requires neither Node.js nor React, and has no frontend asset compilation step.
* **Server-Side Communication:** Flask endpoints use the Requests library to communicate with RadLab services, so the browser does not connect directly to the backend server. The application also converts article Markdown into HTML and calculates text statistics in Python.
* **Two Interface Languages:** Polish and English.
* **Copy and Export:** Copy the generated text to the clipboard or download it as a Markdown (`.md`) file.
* **Transparent Search Scope:** An expandable panel lists the categories and sites available in the index; the section below the article shows the specific news items supplied to create it.
* **Two Source Views:** Browse cards or a compact list, filter by category, and inspect excerpts, crawl dates, and links to the original reports.
* **Topic Suggestions and Regeneration:** Draw fresh suggested questions, edit your query, and create another article. Progress indicators distinguish search from generation; writing the article can take 1–2 minutes.

---

## Access & Links

* **Open the App:** [puls.apps.radlab.dev](https://puls.apps.radlab.dev).
* **Status:** Demo within the RadLab ecosystem.
