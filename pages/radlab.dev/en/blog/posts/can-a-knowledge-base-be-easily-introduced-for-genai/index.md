---
title: "Can a knowledge base be easily introduced for GenAI?"
date: 2025-12-27
slug: can-a-knowledge-base-be-easily-introduced-for-genai
description: "Absolutely—just plug langchain_rag into the llm-router 😉 Intro Hello! Today we are showing additional capabilities of the LLM Router in the form of plugins,…"
categories: ["Bez kategorii"]
image: media/_featured.jpeg
lang: en
translation_of: czy-mozna-w-prosty-sposob-wprowadzic-baze-wiedzy-dla-genai
wp_id: 4270
---

Absolutely—just plug `langchain_rag` into the `llm-router` 😉

![](media/01-2025-12-26_22-20-09_5743.jpeg)

## Intro

Hello! Today we are showing additional capabilities of the LLM Router in the form of plugins, actually just one plugin `langchain_rag`. This is a plugin that creates a local knowledge base from the content provided during the indexing process. It uses well‑known solutions such as `langchain` to create a RAG system and `fais` as a vector knowledge base. Then the created knowledge base can be attached to any query in the LLM Router, without modifying the application that currently uses generative models. What does this approach provide?

The ability to automatically enrich the context passed to the generative model — i.e., the standard RAG approach. It is enough to index the documents you choose using the available CLI command `llm-router-rag-langchain index [OPTIONS]` and all those contents are available to the generative model when generating a response.

> What does this provide?
> The ability to automatically enrich the context passed to the generative model — i.e., the standard RAG approach. It is enough to index the documents you choose using the available CLI command `llm-router-rag-langchain index [OPTIONS]`, and all those contents are available to the generative model when generating a response.

## Indexation

Data indexing is the step in which, from a given directory, files with specified extensions are stored in a local knowledge base. The **knowledge‑base** plugin uses a loaded embedder model (by default configured as`google/embeddinggemma-300m`) to create vector representations of chunked texts and saves them to a locally created **FAISS vector database**. It is the user who chooses which **documents** to use **for** **context enrichment** and in which collections they should be placed. This is an important step because the **accuracy** of the **generative model’s** **responses** depends on the content of this **database**. Despite its importance, the **process** is very **simple**. After installing llm‑router, a **command** for handling the plugin’s knowledge base is available: `llm-router-rag-langchain`. The command is installed in the CLI, so it is **available** from any **router** **directory**.

In today’s example we used all the descriptions from the main repository and sub‑repositories of LLM Router as the knowledge base:

- Main llm-routera repository: md and txt files;
- Plugins repository (including the described plugin) – files in md , txt format;
- Services handling guardrails and maskers plugins – md and txt ;
- Repository with example tools using llm‑router – md and txt files;
- Dedicated graphical interfaces for Anonymizer and Configs Manager – also md and txt files;
- llm-router.cloud website – html , md , and txt files;

For simplicity we added a basic Bash script in which you only need to change the file types and indexing paths and, without modifying any other settings from the main router directory, issue the command \[here [full](https://github.com/radlab-dev-group/llm-router/blob/main/scripts/llm-router-rag-langchain-index.sh) script\]:

```text
bash scripts/llm-router-rag-langchain-index.sh
```

Because of this, a local knowledge base will be saved in the default directory: `workdir/plugins/utils/rag/langchain/sample_collection/`, which can then be attached as the knowledge base in the llm‑router.

## Running the knowledge base in LLM Router

The knowledge base is loaded by default from the directory where the LLM Router is started, but the storage/load location can be set arbitrarily with the environment variable `LLM_ROUTER_LANGCHAIN_RAG_PERSIST_DIR`. For the LLM Router to use the created knowledge base, the `langchain_rag` plugin must be activated and the path to the created knowledge base must be set. After starting the router with such a configuration, every query to the generative model will be enriched with context from the attached knowledge base. Activating the plugin simply means exporting the environment variable with utils‑type plugins when launching the router (the default [scipt](https://github.com/radlab-dev-group/llm-router/blob/main/run-rest-api-gunicorn.sh)  allows modification).

```text
export LLM_ROUTER_UTILS_PLUGINS_PIPELINE="langchain_rag"
```

And that’s basically it—if you don’t modify parameters such as context size or the embedder, there’s nothing you need to change or configure—just index your own data 🙂 How it looks in practice. Below, in the screenshot, is the model’s response without the attached *langchain\_rag* plugin, with the indexed content:

![Obrazek posiada pusty atrybut alt - plik: image-4-926x1024.avif](media/02-image-4.png)

And the response with the plugin attached:

![](media/03-image-2.png)

## Outro

And to wrap up, here’s a console video showing how to index the mentioned content:

{{< video media/llm-router-rag-langchain-indexing.webm >}}

and switching the router to operate in knowledge‑base mode (the beginning of the video shows the router running without a knowledge base, the second part shows it running with an attached knowledge base):

{{< video media/llm-router-rag-langchain.webm >}}

Starring: *OpenWeb UI* with the *LLM‑Router* attached (with the *langchain\_rag* plugin *disabled* and *enabled*).
**We encourage you to download, try it out, and share your impressions of using it 🙂**

---

> **Related Products:** Knowledge-base context augmentation is natively supported via the plugin ecosystem of [LLM Router](/en/products/llm-router/). You can also explore live demonstrations on [RDL Playground AI](/en/products/playground/).
