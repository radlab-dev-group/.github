---
title: "3c Polarization – model from plg on HF"
date: 2025-06-01
updated: 2025-09-26
slug: polaryzacja-3c-model-z-plg-na-hf
description: "Hello 😉 Today, we are presenting and publishing an element of the playground’s. It is a classification model whose task is to determine the polarity of texts.…"
tags: ["3c", "polaryzacja"]
categories: ["experiment", "huggingface", "models", "transformers"]
image: media/polaryzacja-3c-model-z-plg-na-hf/_featured.avif
lang: en
translation_of: polaryzacja-3c-model-z-plg-na-hf
wp_id: 3182
---

Hello 😉 Today, we are presenting and publishing an element of the [playground’s](https://playground.radlab.dev/). It is a classification model whose task is to determine the [polarity of texts](https://huggingface.co/radlab/polarity-3c). We are publishing the model on our [huggingface](https://huggingface.co/radlab) 😉 We define polarities as:

- positive — the model assigns this class if the information in the texts can evoke positive emotions/feelings;
- negative — if the information in the texts evokes negative feelings;
- ambivalent/neutral — if the information is neutral or evokes conflicting feelings at the same time;

![](@media/polaryzacja-3c-model-z-plg-na-hf/01-image-2.avif)

### Process: data and learning

The model was developed in two stages. However, unlike the standard approach (starting with annotation), we began by training the model based on existing annotations (hm… that’s nothing new… yes and no…). However, when looking for a dataset for polarization, most often these are datasets related to opinions on a given topic. In our case, it is not about determining the polarization of opinions (e.g., *This product can be thrown in the trash! or I recommend this doctor because he has a very good approach to patients!*), but about determining the polarization of information that the *media* (websites) feed us.

So we had to look elsewhere 😉 The choice was not so obvious, but it reflected the idea of polarization of information rather than opinion… and we settled on PlWordNet Emo. PlWordNet Emo is a selected part of PlWordNet’s marked with emotions (and more) (the markings are at the level of word meanings) — I recommend familiarizing yourself with what [EmoPlWordNet](http://plwordnet.pwr.wroc.pl/wordnet/)  is — it is a very valuable source of information. After a few technical steps, we transformed the examples of usage into meanings with emotional descriptions, and then into an approximate set of emotional polarization (reduction of emotions and granulation to 3 – positive, negative, ambivalent). Below are a few examples from the set, after conversion:

![](@media/polaryzacja-3c-model-z-plg-na-hf/02-image-3.avif)

We used this collection to train the *polarity3c-zero* model, which was immediately used in the decision support process during annotation. The model provided real-time annotation suggestions for two annotators. This resulted in a collection of approximately 3,500 manual annotations, which were used for the final training of the model.

The final model is a simple architecture in which a simple classification layer (*ClassificationHead*) is added above the language model, which is trained to determine polarity. Classification layer architecture:

```text
  (classifier): RobertaClassificationHead(
    (dense): Linear(in_features=1024, out_features=1024, bias=True)
    (dropout): Dropout(p=0.1, inplace=False)
    (out_proj): Linear(in_features=1024, out_features=3, bias=True)
  )
```

1024 on the first dense layer of Linear is the output of the base model  [polish-roberta-large-v2](https://huggingface.co/sdadas/polish-roberta-large-v2), the output of the *polarity3c* model, is the layer marked (out\_proj), which has 3 features at the output, i.e., our detected classes. The charts below show the basic metrics from training this model:

![](@media/polaryzacja-3c-model-z-plg-na-hf/03-image-1.avif)

### Launch and testing

The easiest way to run the model is to use the *[transformers](https://huggingface.co/docs/transformers)* library with a *[pipeline’a](https://huggingface.co/docs/transformers/pipeline_tutorial)*.

```python
from transformers import pipeline

classifier = pipeline(model="radlab/polarity-3c", task="text-classification")
```

The use of the model is equally simple:

```text
 classifier("Po upadku reżimu Asada w Syrii, mieszkańcy, borykający się z ubóstwem, zaczęli tłumnie poszukiwać skarbów, zachęceni legendami o zakopanych bogactwach i dostępnością wykrywaczy metali, które stały się popularnym towarem. Mimo, że działalność ta jest nielegalna, rząd przymyka oko, a sprzedawcy oferują urządzenia nawet dla dzieci. Poszukiwacze skupiają się na obszarach historycznych, wierząc w legendy o skarbach ukrytych przez starożytne cywilizacje i wojska osmańskie, choć eksperci ostrzegają przed fałszywymi monetami i kradzieżą artefaktów z muzeów.")
```

In response, we will receive the value:

```json
[{'label': 'ambivalent', 'score': 0.9994786381721497}]
```

To read the full confidence distribution of the model, simply add the option specifying how many labels with the highest probability you want to receive. In our case, we have 3 labels, so we add the option `top_k=3`  to the`classifier` to receive information about all classes:

```text
 classifier("Po upadku reżimu Asada w Syrii, mieszkańcy, borykający się z ubóstwem, zaczęli tłumnie poszukiwać skarbów, zachęceni legendami o zakopanych bogactwach i dostępnością wykrywaczy metali, które stały się popularnym towarem. Mimo, że działalność ta jest nielegalna, rząd przymyka oko, a sprzedawcy oferują urządzenia nawet dla dzieci. Poszukiwacze skupiają się na obszarach historycznych, wierząc w legendy o skarbach ukrytych przez starożytne cywilizacje i wojska osmańskie, choć eksperci ostrzegają przed fałszywymi monetami i kradzieżą artefaktów z muzeów.", top_k=3)
```

And here’s the way out:

```json
[{'label': 'ambivalent', 'score': 0.9994786381721497},
 {'label': 'negative', 'score': 0.0002675618161447346},
 {'label': 'positive', 'score': 0.0002538080152589828}]
```

### Outro

The model has been available on our  [playground’s](https://playground.radlab.dev/) since July last year. We collect data on its performance, which can be viewed in the [statistics](https://playground.radlab.dev/Statystyki). Information about polarization is also added to each [new stream](https://playground.radlab.dev/Strumie%C5%84_Aktualno%C5%9Bci) using this model. The model is, of course, available for free on our HF:[ here is the model. ](https://huggingface.co/radlab/polarity-3c)

---

> **Related solutions:** This model powers sentiment and polarity analytics in [Radar Informacji](/en/products/radar/) and the live news stream on [RDL Playground AI](/en/products/playground/).

## Unlock the potential of your data with our ML/NLP. Bon appetit! 😉
