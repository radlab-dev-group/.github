---
title: "Polaryzacja 3c – model z plg na HF"
date: 2025-06-01
slug: polaryzacja-3c-model-z-plg-na-hf
description: "Intro Witajcie 😉 Dzisiaj przedstawiamy i upubliczniamy element działania playgroundu. Jest to model klasyfikacyjny, którego zadaniem jest określanie…"
tags: ["3c", "polaryzacja"]
categories: ["eksperyment", "huggingface", "model", "transformatory"]
image: media/polaryzacja-3c-model-z-plg-na-hf/_featured.avif
lang: pl
wp_id: 3182
---

## Intro

Witajcie 😉 Dzisiaj przedstawiamy i upubliczniamy element działania [playgroundu](https://playground.radlab.dev/). Jest to model klasyfikacyjny, którego zadaniem jest [określanie polaryzacji tekstów](https://huggingface.co/radlab/polarity-3c). Model upubliczniamy na naszym [huggingface](https://huggingface.co/radlab) 😉 Polaryzacje określamy jako:

- pozytywna — model przypisuje tę klasę, jeżeli informacje w tekstach mogą wzbudzić pozytywne emocje/odczucia;
- negatywna — jeżeli informacje w tekstach wzbudzają pozytywne odczucia;
- ambiwalentna/neutralna — jeżeli informacja jest obojętna lub wywołuje przeciwstawne odczucia w tym samym czasie;

![](@media/polaryzacja-3c-model-z-plg-na-hf/01-image-2.avif)

## Proces: dane i uczenie

Model powstawał w dwóch etapach. W odróżnieniu jednak od standardowego podejścia (start od anotacji), rozpoczęliśmy jednak od uczenia modelu na podstawie istniejących już anotacji (hm… to nic nowego przecież… *i tak i nie…*). Jednak szukając zbioru danych do polaryzacji, najczęściej są to zbiory dotyczące opinii na jakiś temat. W naszym przypadku nie chodzi o określenie polaryzacji opinii (np. *Ten produkt można wyrzucić do kosza!* lub *Polecam lekarza bo ma bardzo dobre podejście do pacjenta!*) a określenie polaryzacji informacji, którą wtłaczają w nas *media* (serwisy internetowe).

Zatem należało szukać w innym miejscu 😉 Wybór nie był aż tak oczywisty, ale oddający bardziej ideę polaryzacji informacji, niż opinii… i padło na *Słowosieć Emo*. Słowosieć Emo, to oznaczona za pomocą emocji (i nie tylko) wybrana część [Słowosieci](http://plwordnet.pwr.wroc.pl/wordnet/) (oznaczenia są na poziomie znaczeń słów) — polecam zapoznać się czym jest Słowosieć — to bardzo cenne źródło informacji. Po kilku technicznych krokach, przekształcone przykłady użycia do znaczeń z opisem emocjonalnym, przekształciliśmy w przybliżony zbiór polaryzacji emocjonalnej (redukcja emocji i granulacji do 3 – *pozytywna*, *negatywna*, ambiwalentna). Poniżej na zdjęciu kilka przykładów ze zbioru, już po konwersji:

![](@media/polaryzacja-3c-model-z-plg-na-hf/02-image-3.avif)

Ten zbiór wykorzystaliśmy do wyuczenia modelu *polarity3c-zero*, czyli modelu, który wykorzystany został od razu w procesie wspierania decyzji podczas anotacji. Model w czasie rzeczywistym proponował propozycje anotacji dla dwóch anotatorów. W ten sposób powstał zbiór około 3500 ręcznych anotacji, które wykorzystane były do finalnego uczenia modelu.

Finalny model, to prosta architektura, w której nad modelem językowym dodana jest prosta warstwa klasyfikacyjna (*ClassificationHead*), która wyuczana jest do określania polaryzacji. Architektura warstwy klasyfikacyjnej:

```text
  (classifier): RobertaClassificationHead(
    (dense): Linear(in_features=1024, out_features=1024, bias=True)
    (dropout): Dropout(p=0.1, inplace=False)
    (out_proj): Linear(in_features=1024, out_features=3, bias=True)
  )
```

1024 na pierwszej gęstej warstwie Liniowej to wyjście modelu bazowego [polish-roberta-large-v2](https://huggingface.co/sdadas/polish-roberta-large-v2), wyjście modelu polarity3c, to warstwa oznaczona (out\_proj), która na wyjściu ma 3 cechy, czyli nasze wykrywane klasy. Na wykresach poniżej przedstawiamy podstawowe metryki z uczenia tego modelu:

![](@media/polaryzacja-3c-model-z-plg-na-hf/03-image-1.avif)

## Uruchomienie i testowanie

Najprościej uruchomić model za pomocą biblioteki *[transformers](https://huggingface.co/docs/transformers)* z wykorzystaniem *[pipeline’a](https://huggingface.co/docs/transformers/pipeline_tutorial)*.

```python
from transformers import pipeline

classifier = pipeline(model="radlab/polarity-3c", task="text-classification")
```

Samo użycie modelu jest równie proste:

```text
 classifier("Po upadku reżimu Asada w Syrii, mieszkańcy, borykający się z ubóstwem, zaczęli tłumnie poszukiwać skarbów, zachęceni legendami o zakopanych bogactwach i dostępnością wykrywaczy metali, które stały się popularnym towarem. Mimo, że działalność ta jest nielegalna, rząd przymyka oko, a sprzedawcy oferują urządzenia nawet dla dzieci. Poszukiwacze skupiają się na obszarach historycznych, wierząc w legendy o skarbach ukrytych przez starożytne cywilizacje i wojska osmańskie, choć eksperci ostrzegają przed fałszywymi monetami i kradzieżą artefaktów z muzeów.")
```

W odpowiedzi dostaniemy wartość

```json
[{'label': 'ambivalent', 'score': 0.9994786381721497}]
```

Aby odczytać pełen rozkład pewności modelu, wystarczy dodać opcję ile labelek o najwyższym prawdopodobieństwie chcemy otrzymać. W naszym przypadku mamy 3 labelki, dlatego do `classifier` dodajemy opcje `top_k=3` aby otrzymać informacje o wszystkich klasach:

```text
 classifier("Po upadku reżimu Asada w Syrii, mieszkańcy, borykający się z ubóstwem, zaczęli tłumnie poszukiwać skarbów, zachęceni legendami o zakopanych bogactwach i dostępnością wykrywaczy metali, które stały się popularnym towarem. Mimo, że działalność ta jest nielegalna, rząd przymyka oko, a sprzedawcy oferują urządzenia nawet dla dzieci. Poszukiwacze skupiają się na obszarach historycznych, wierząc w legendy o skarbach ukrytych przez starożytne cywilizacje i wojska osmańskie, choć eksperci ostrzegają przed fałszywymi monetami i kradzieżą artefaktów z muzeów.", top_k=3)
```

A oto i wyjście:

```json
[{'label': 'ambivalent', 'score': 0.9994786381721497},
 {'label': 'negative', 'score': 0.0002675618161447346},
 {'label': 'positive', 'score': 0.0002538080152589828}]
```

## Outro

Model udostępniony jest od lipca ubiegłego roku na naszym playgroundzie. Zbieramy efekty jego działania, które można podejrzeć w [statystykach](https://playground.radlab.dev/Statystyki). Na [strumieniu](https://playground.radlab.dev/Strumie%C5%84_Aktualno%C5%9Bci) przy każdym newsie, dodawana jest również informacja o polarzyacji, właśnie przez ten model. Model oczywiście za free na naszych HF: [Klik do modelu](https://huggingface.co/radlab/polarity-3c).

---

> **Powiązane rozwiązania:** Model ten stanowi integralną część analizy sentymentu w [Radarze Informacji](/products/radar/) oraz strumienia wiadomości na platformie [RDL Playground AI](/products/playground/).
