---
title: "Narzędzia do tworzenia modeli word2vec"
date: 2021-06-22
updated: 2024-04-27
slug: narzedzia-do-tworzenia-modeli-word2vec
description: "Fasttext,…"
categories: ["narzędzia", "word2vec"]
image: media/_featured.png
lang: pl
wp_id: 2071
---

### Fasttext

###### Informacje wstępne

Do pobrania z: [https://fasttext.cc/](https://fasttext.cc/)
Samouczek (reprezentacja słów): [https://fasttext.cc/docs/en/unsupervised-tutorial.html](https://fasttext.cc/docs/en/unsupervised-tutorial.html)

###### Format wejściowy

Wejściem jest plik tekstowy, w którym kolejne wiersze reprezentują kolejne teksty, zdania, frazy. Przykładowo:

```text
 awokado przekrawać na pół usuwać pestka i wydrążać miąższ
 dziś niemiecki i musieć zaliczyć
 gra rozpoczynać jeden z gracz ciągnąć karta z stos karta zakryć lub z stos odkryty
```

###### Przykładowe wywołanie

```text
 ./fasttext skipgram -minCount 5 \
   -lr 0.05 -ws 5 -epoch 10 \
   -input input-corpora-file.txt \
   -output output-corpora-file-model
```

### GloVe

- https://nlp.stanford.edu/projects/glove/
- https://www.aclweb.org/anthology/D14-1162.pdf
- https://nlp.stanford.edu/projects/glove/
