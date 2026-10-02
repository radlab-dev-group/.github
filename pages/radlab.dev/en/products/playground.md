---
title: "RDL Playground AI"
subtitle: "An AI testing ground for analysing and summarising news"
slug: "playground"
description: "RDL Playground AI is a non-profit research project demonstrating automated news analysis: Polish-language summaries, articles generated in response to questions, and daily information overviews with sources. It runs locally and requires no account."
icon: "flask"
status: "Research Platform · Non-Profit"
version: "Live Web App"
tags: ["NLP", "News Stream", "Summarization", "Information Retrieval", "Local Processing"]
actions:
  - {label: "Launch Playground (playground.radlab.dev)", href: "https://playground.radlab.dev", style: primary}
  - {label: "Experiments & methods on the blog", href: "/en/blog/", style: quiet}
---

## What is RDL Playground AI?

**RDL Playground AI** is RadLab’s testing ground for applying artificial intelligence methods to online news. It is a non-profit research project available without creating an account.

Content collection, processing, analysis, and presentation are automated. People supervise the system, with additional methods and models supporting that oversight.

---

## What Can You Explore?

### 1. News Stream
Short summaries of news from Polish and international outlets, presented in Polish regardless of the source language. The system collects, analyses, summarises, and indexes content for further retrieval.

Before publication, a summary must pass checks including similarity to the original for plagiarism detection and topic consistency with the source article. The stream displays recent news rather than a full archive.

### 2. News Creator
Ask a question about current news, and the Creator prepares an article summarising relevant reports. You can select the last **1, 2, or 3 days** as the source period.

The article comes with a list of source pages and result statistics, including a polarity chart for the analysed texts. This lets you consult the sources and inspect the tone of the material used for the answer.

### 3. Information Browser
Automatically identifies topics in the media and presents a daily overview of key information. Each analysis covers the previous day — it is not a live view.

Each item includes a topic name, a summary based on a data sample, and its sources.

---

## Local Processing and Small Models

The entire solution runs locally. Analysed content is not sent to external services, and news data is stored locally and is not used commercially.

The Playground demonstrates what can be achieved with budget hardware — up to **PLN 6,500 including tax**, according to the project description. It uses small generative models with up to **12 billion parameters**, fitting on a graphics card with **24 GB of memory** while leaving room for context. This is a deliberate constraint of the experiment, not a showcase of the largest models.

---

## Access and Experiment Details

* **Application:** [playground.radlab.dev](https://playground.radlab.dev) — no account required.
* **Experiments and methods:** [RadLab blog](/en/blog/).
