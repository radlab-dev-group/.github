---
title: "Extraction QA – our model polish-qa-v2"
date: 2024-04-15
updated: 2025-09-24
slug: ekstrakcyjne-qa-nasz-model-polish-qa-v2
description: "In the field of natural language processing, innovative solutions are constantly emerging that enable precise answers to questions in different languages. We…"
categories: ["huggingface", "models", "Q&A", "transformers"]
image: media/ekstrakcyjne-qa-nasz-model-polish-qa-v2/_featured.png
lang: en
translation_of: ekstrakcyjne-qa-nasz-model-polish-qa-v2
wp_id: 2213
---

In the field of natural language processing, innovative solutions are constantly emerging that enable precise answers to questions in different languages. We present the [polish-qa-v2](https://huggingface.co/radlab/polish-qa-v2) model, which represents a step forward in our research on matching questions with answers using large language models.

The [polish-qa-v2](https://huggingface.co/radlab/polish-qa-v2) model is an example of an extractive QA model that specializes in extracting the most relevant fragment of text to provide a precise answer to a question. Unlike generative models, which create answers from scratch, extractive models limit themselves to selecting existing text fragments as answers to questions.

## Example of use

```python
from transformers import pipeline
model_path = "radlab/polish-qa-v2"
question_answerer = pipeline(
  "question-answering",
  model=model_path
)
question = "Jakie silniki posiadał okręt?"
context = """Okręt był napędzany przez trzy trzycylindrowe maszyny parowe potrójnego rozprężania, które napędzały poprzez wały napędowe trzy śruby napędowe (dwie trójskrzydłowe
zewnętrzne o średnicy 4,5 metra i czteroskrzydłową o średnicy 4,2 metra).
Para była dostarczana przez cztery kotły wodnorurkowe typu Marine,
wyposażone łącznie w osiem palenisk i osiem kotłów cylindrycznych,
które miały łącznie 32 paleniska. Ciśnienie robocze kotłów wynosiło 12 at,
a ich łączna powierzchnia grzewcza 3560 m². Wszystkie kotły były opalane węglem,
którego normalny zapas wynosił 650, a maksymalny 1070 ton.
Nominalna moc siłowni wynosiła 13 000 KM (maksymalnie 13 922 KM przy 108 obr./min),
co pozwalało na osiągnięcie prędkości maksymalnej od 17,5 do 17,6 węzła.
Zasięg wynosił 3420 mil morskich przy prędkości 10 węzłów. Zużycie węgla przy mocy 10 000 KM
wynosiło około 11 ton na godzinę, a przy mocy maksymalnej 16 ton na godzinę.
"""
print(
  question_answerer(
    question=question,
    context=context.replace("\n", " ")
  )
)
```

After executing the above code, the following result is obtained:

```python
{
  'score': 0.612459123134613,
  'start': 25,
  'end': 84,
  'answer': ' trzy trzycylindrowe maszyny parowe potrójnego rozprężania,'
}
```

The experiment is based on the [sdadas/polish-roberta-large-v2](https://huggingface.co/sdadas/polish-roberta-large-v2) model, which we trained on the [clarin-pl/poquad](https://huggingface.co/datasets/clarin-pl/poquad) dataset. Training took 2 hours on a single RTX 3090 Ti graphics card.

polish-qa-v2 is available at [https://huggingface.co/radlab/polish-qa-v2](https://huggingface.co/radlab/polish-qa-v2), where you can test it without having to run it locally. For those interested, we provide the entire model for download at the same link.

We invite you to read.
