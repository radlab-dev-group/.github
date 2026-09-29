---
title: "pLLama3.1 8B — medium-sized and even small GenAI for Polish"
date: 2024-12-08
updated: 2025-10-24
slug: pllama3-1-8b-czyli-srednio-duze-a-nawet-male-genai-dla-polskiego
description: "Yes… it was intentional to misspell not-in-or-de-r (it’s not a mistake) as a preview of the next version of the model 🙂 Between pLlamą3 and pLlamą3.2, there…"
tags: ["dpo", "fine-tuning", "genai", "huggingface", "llm", "pllama", "transformers"]
categories: ["experiment", "GenAI", "llama", "models", "transformers"]
image: media/pllama3-1-8b-czyli-srednio-duze-a-nawet-male-genai-dla-polskiego/_featured.png
lang: en
translation_of: pllama3-1-8b-czyli-srednio-duze-a-nawet-male-genai-dla-polskiego
wp_id: 2680
---

Yes… it was intentional to misspell **not-in-or-de-r** (it’s not a mistake) as a preview of the next version of the model 🙂 Between [pLlamą3](https://radlab.dev/2024/08/16/pllama3-8b-70b-genai-dla-polskiego/) and [pLlamą3.2](https://radlab.dev/2024/10/20/pllama3-2-1b-3b-male-genai-dla-polskiego/), there was also a version called pLLama3.1 — and that’s what today’s post is about.

![pLLama - wygenerowane za pomocą AI](@media/pllama3-8b-70b-genai-dla-polskiego/01-image.png)

*pLLama – generated using AI*

We recently wrote:

![](https://en.radlab.dev/wp-content/uploads/2024/12/image-3.avif)

### Intro

Another version of Meta’s model that speaks better Polish! In this post, we present the  [pLLama3.1](https://huggingface.co/collections/radlab/pllama31-models-6710cace79670d489fe7d9bd) model in 8B architecture. This time, we have published the –*content model*, which is a less talkative version of the model, the –*chat* model as a more talkative version, the pure –*base model* after LoR, but we have also made available an *experimental model with the transfer of adaptive* layers from the pLLama3 model to the pLLama3.1 model (more on that in a future post :)). All models are of course available on [huggingface](https://huggingface.co/radlab) (full [collection of 3.1 models](https://huggingface.co/collections/radlab/pllama31-models-6710cace79670d489fe7d9bd)):

- Model radlab/pLLama3.1-8B-content : this is an SFT model, and DPO provides short and concise answers.
- Model radlab/pLLama3.1-8B-chat model is a more talkative version of the model (after SFT and DPO), ideal for chatting.
- Model radlab/pLLama3.1-8B-base-ft-16bit is a model directly after SFT with LoRa.
- Eksperimental model radlab/pLLama-L31-adapters-MIX-SFT-DPO with transfer of adaptive layers between models.

### Dataset, learning, and graphs

All versions of the pLLama3.1 models have one parent, namely [Llama-3.1-8B-Instruct](https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct) from Meta.AI in the 8B architecture. This model already writes quite well in its basic version in Polish, but it still has a long way to go before it can write (at least) correctly. Hence the idea: let’s train this model too 🙂

For training, we used a dataset developed for earlier models. To briefly recap, this is over 650k instructions generated automatically based on available datasets. We converted each set (e.g., marked with parts of speech) into system prompts in the form of questions and answers. This resulted in a set of instructions that we used as data to train the model. We also developed a set of instructions for DPO based on available language corpora, including NKJP and KPWr.

Due to hardware limitations, we performed SFT using adaptive layers (LoRA) with 16-bit quantization (bits and bytes). Similarly, in DPO, the base model was loaded as a quantized version of pLLama3.1 after SFT, and the adaptive layer was also retrained during DPO. As a reminder, in our case, during SFT, we skew the model weights towards the Polish language, while in the DPO process, we teach the model to generate text correctly in terms of grammar and punctuation. We trained the models on single RTX 4090 graphics cards (24 GB). SFT (LoRA) lasted 14d 2h 3m and 52s. DPO lasted 2d 15h 2m  and 42s. The difference between the –*content* and –*chat* models is a matter of a different way of combining the adaptation layer with the model (but this will be discussed in a separate post). Below are two graphs, the first showing the loss function value in SFT, and the second showing the *chosen and rejected* logit values during DPO.

Loss function during SFT with Lora:

![](@media/pllama3-1-8b-czyli-srednio-duze-a-nawet-male-genai-dla-polskiego/03-image-1.avif)

In the DPO process:

![](@media/pllama3-1-8b-czyli-srednio-duze-a-nawet-male-genai-dla-polskiego/04-image.avif)

### Outro

How does version 3.1 differ from the  [pLLama3](https://radlab.dev/2024/08/16/pllama3-8b-70b-genai-dla-polskiego/) model? First and foremost, in terms of context size. The pLLama3 model had a limited context of 8k tokens. The pLLama3.1 version has a context length of 128k tokens (this results from the base model, i.e., in pLLama 3, we trained Llama3 from Meta, while in pLLama3.1, we trained the LLama3.1 model from Meta). In RAG tests, pLLama3.1 performs significantly better than version 3, mainly due to its larger context. At the moment, when answering a question, the model is able to accommodate much more information, which significantly reduces the frequency of its querying, greatly reduces the problem of too frequent querying of the model, dividing the data to the size of the input (and, incidentally, reduces the problem of compiling the final answer in RAG based on partial answers with a small context).

And as an addition to HuggingFace, we have a model that we call L31 ([pLLama-L31-adapters-MIX-SFT-DPO](https://huggingface.co/radlab/pLLama-L31-adapters-MIX-SFT-DPO)) as an experiment in mixing models.

That’s all for today, thanks!

## Unlock the potential of your data with our ML/NLP. Bon appetite! 😉
