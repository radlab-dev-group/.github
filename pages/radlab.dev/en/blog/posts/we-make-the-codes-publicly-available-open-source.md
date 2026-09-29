---
title: "We make the codes publicly available – open source."
date: 2025-09-27
updated: 2025-09-28
slug: we-make-the-codes-publicly-available-open-source
description: "Hello! Today we will describe the technical aspects. Over the past month, we have been working on publishing some of our solutions. Today we would like to…"
tags: ["github", "huggingface", "llm", "method", "ml", "python", "transformers"]
categories: ["embedding", "experiment", "github", "huggingface", "method", "repository"]
lang: en
translation_of: upubliczniamy-kody
wp_id: 4104
---

Hello! Today we will describe the technical aspects. Over the past month, we have been working on [publishing](https://github.com/radlab-dev-group) some of our solutions. Today we would like to present a few of them. Some of them are working mechanisms on the [playground](https://playground.radlab.dev/), others are ideas implemented “on the side.” We have returned to the idea of developing solutions completely publicly on [GitHub](https://github.com/radlab-dev-group). Therefore, we invite you to visit our GitHub profile, which we briefly present in this post 😉

![](https://en.radlab.dev/wp-content/uploads/2025/09/2025-09-26_17-03-51_7632-1024x796.avif)

Below are the projects with brief descriptions. Each of them has a fairly extensive README file on  [Github](https://github.com/radlab-dev-group).

## relgat – projector (“from the side”)

The repository ([clic](https://github.com/radlab-dev-group/relgat-projector)) contains a proprietary implementation of link-prediction mechanisms based on semantic graphs. The idea was to recreate semantic relationships and enable the creation of new representations based on existing ones. We assume that nodes in the graph have a semantic description (e.g., using *embedding*), while edges have no description but are distinguishable from each other. The *edge label* in such a graph denotes the *name of the relation*.

The method enables learning transformation matrices for edges in the graph based on the node environment. The model simultaneously learns the transformations of each relation separately and learns to define nodes based on those existing in the graph. A node is defined by its neighborhood (input); we assume that what enters a given node defines it. Unlike standard RelGAT, we do not learn the entire network—we learn transformations of the base space to the same space in such a way that for \[`A -> rel1 -> B`\], \[`C -> rel2 -> B`\] we look for transformations `rel1` i `rel2` o that the combination of embeddings `A` i `C` gives embedding `B`. By additionally using evaluation by metrics such as *hits@X* as loss functions, we additionally learn link prediction. This will make it possible to transform any vector `X` from the learned space) using a transformation matrix `M` (e.g., by activating specific relations) in such a way as to obtain vector `X`‘ in the same space, but after transformation by relations.

We have already completed a series of experiments (the charts show the latest stable training sessions) and so far (according to the charts) it looks promising 😉

![](https://en.radlab.dev/wp-content/uploads/2025/09/image-16-1024x467.avif)

![](https://en.radlab.dev/wp-content/uploads/2025/09/image-1-1024x162.avif)

## [plwordnet](https://github.com/radlab-dev-group/plwordnet) (“from the side”)

This repository ([clic](https://github.com/radlab-dev-group/plwordnet)) can be used to operate on the Polish and English [Wordnet](http://plwordnet.pwr.wroc.pl/wordnet/) (Wordnet – Polish, Princeton Wordnet – English). Although it is not currently used only for browsing wordnet’s, it is primarily a mechanism for creating data sets. A method for creating embeddings for semantic graph nodes is implemented there. It contains the entire process from downloading Wordnet, preparing data for further processing, to: creating

- a semantic embedder,
- embedding representations for the meanings of PLWordnet and Princeton Wordnet using this embedder.

On the [huggingface](https://huggingface.co/radlab) platform we have published the first version of the  [model](https://huggingface.co/radlab/semantic-euro-bert-encoder-v1) ([radlab/semantic-euro-bert-encoder-v1](https://huggingface.co/radlab/semantic-euro-bert-encoder-v1)). It is a bilingual embedder model in which we used [EuroBERT](https://huggingface.co/EuroBERT) as the language model. Creating embedding representations is a multi-step process. First, representations are created for lexical units. Then, for those units for which no representation could be created but which are found in a synset that contains some representations, a (*fake*) representation is created for the unit. Then, for each synset that has at least one representation of a unit, embedding representations are created as weighted averages of the embedding’s of the units. After this operation, not all units and synsets have definitions, which is why the [relgat-projector](https://github.com/radlab-dev-group/relgat-projector) is to be used, among other things, to transform a node without a representation but with some environment (synset or unit).

## [ml-utils (“from the side”)](https://github.com/radlab-dev-group/ml-utils)

Earlier libraries are based on [ml-utils](https://github.com/radlab-dev-group/ml-utils). This is a library that simplifies the processing process in the context of machine learning. It contains general classes and methods that are independent of the project, but their functionality can be shared with other projects. Thanks to [ml-utils](https://github.com/radlab-dev-group/ml-utils), you can, among other things:

- Easily manage the logging of results to Weights & Biases,
- manage prompts for generative models using directory-based names,
- support any OpenAPI-compliant generative model API, create queues, and cache responses to reduce the number of model queries.

Additionally, general-purpose modules are available, such as *env* parsing and creating unified loggers, as well as a module for downloading data from [Wikipedia](https://github.com/radlab-dev-group/ml-utils/blob/main/rdl_ml_utils/utils/wikipedia.py), which is used in [plwordnet](https://github.com/radlab-dev-group/plwordnet) to enrich the context of built embeddings.

## Modules from the playground

In the [clusterer](https://github.com/radlab-dev-group/clusterer) repository, we’ve included a module responsible for creating clusters on the [Playground](https://playground.radlab.dev/). The types of information visible in the *[Information Browser](https://radlab.dev/2025/05/28/przegladarka-informacji/)* or *[Information Explorer](https://radlab.dev/2025/07/14/eksplorator-informacji-nie-mlotek-a-skalpel/)* are created using this module. A more detailed description of the method is available on the blog in the linked articles. We’ve also released the code for the[ graph visualizer](https://github.com/radlab-dev-group/graph-visualizer), currently running at [https://graph.playground.radlab.dev/](https://graph.playground.radlab.dev/), which presents continuous and discontinuous information graphs. We’ve also included the [radlab-playground-ui](https://github.com/radlab-dev-group/radlab-playground-ui) repository with the [Playground](https://playground.radlab.dev/) interface code as a Streamlite application.

## Summary

All code is available under the [Apache 2.0](https://www.apache.org/licenses/LICENSE-2.0) open source license and is free for commercial and non-commercial use. End. 😉
