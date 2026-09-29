---
title: "Ekstrakcyjne QA – nasz model polish-qa-v2"
date: 2024-04-15
updated: 2024-08-18
slug: ekstrakcyjne-qa-nasz-model-polish-qa-v2
description: "W dziedzinie przetwarzania języka naturalnego stale pojawiają się innowacyjne rozwiązania, które umożliwiają precyzyjne odpowiadanie na pytania w różnych…"
categories: ["huggingface", "model", "Q&A", "transformatory"]
image: media/ekstrakcyjne-qa-nasz-model-polish-qa-v2/_featured.png
lang: pl
wp_id: 2213
---

W dziedzinie przetwarzania języka naturalnego stale pojawiają się innowacyjne rozwiązania, które umożliwiają precyzyjne odpowiadanie na pytania w różnych językach. Prezentujemy [model polish-qa-v2](https://huggingface.co/radlab/polish-qa-v2), który stanowi krok naprzód w naszych badaniach nad dziedziną kojarzenia pytań z odpowiedziami przy użyciu wielkich modeli językowych.

Model [polish-qa-v2](https://huggingface.co/radlab/polish-qa-v2) to przykład modelu ekstrakcyjnego QA, który specjalizuje się w wydobyciu najbardziej istotnego fragmentu tekstu celu udzielenia precyzyjnej odpowiedzi na pytanie. W przeciwieństwie do modeli generatywnych, które tworzą odpowiedzi od podstaw, modele ekstrakcyjne ograniczają się do wybierania istniejących fragmentów tekstu jako odpowiedzi na pytania.

## Przykład użycia

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

Po wykonaniu powyższego kodu, uzyskuje się następujący wynik:

```python
{
  'score': 0.612459123134613,
  'start': 25,
  'end': 84,
  'answer': ' trzy trzycylindrowe maszyny parowe potrójnego rozprężania,'
}
```

Podstawę eksperymentu stanowi model [sdadas/polish-roberta-large-v2](https://huggingface.co/sdadas/polish-roberta-large-v2), który dotrenowaliśmy na zbiorze danych [clarin-pl/poquad](https://huggingface.co/datasets/clarin-pl/poquad). Trening trwał 2 godziny na pojedynczej karcie graficznej RTX 3090 Ti.

polish-qa-v2 dostępny jest na [https://huggingface.co/radlab/polish-qa-v2](https://huggingface.co/radlab/polish-qa-v2), gdzie istnieje możliwość jego przetestowania, bez potrzeby uruchamiania lokalnie. Dla zainteresowanych udostępniamy pod tym samym linkiem cały model do pobrania.
