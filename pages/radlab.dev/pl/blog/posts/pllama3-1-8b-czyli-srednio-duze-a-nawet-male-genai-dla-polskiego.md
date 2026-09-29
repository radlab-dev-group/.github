---
title: "pLLama3.1 8B — czyli średnio-duże a nawet małe GenAI dla Polskiego"
date: 2024-12-08
slug: pllama3-1-8b-czyli-srednio-duze-a-nawet-male-genai-dla-polskiego
description: "pLLama – wygenerowane za pomocą AI Ostatnio napisaliśmy: Tak… celowe było błędne zapisanie nie-ko-po-le-i (to nie błąd) jako zapowiedź nie-kolejnej wersji…"
tags: ["dpo", "fine-tuning", "genai", "huggingface", "llm", "pllama", "transformers"]
categories: ["eksperyment", "GenAI", "llama", "model", "transformatory"]
image: media/pllama3-1-8b-czyli-srednio-duze-a-nawet-male-genai-dla-polskiego/_featured.png
lang: pl
wp_id: 2680
---

![pLLama - wygenerowane za pomocą AI](@media/pllama3-8b-70b-genai-dla-polskiego/01-image.png)

*pLLama – wygenerowane za pomocą AI*

Ostatnio napisaliśmy:

![](@media/pllama3-1-8b-czyli-srednio-duze-a-nawet-male-genai-dla-polskiego/02-image-2.avif)

Tak… celowe było błędne zapisanie **nie-ko-po-le-i** (to nie błąd) jako zapowiedź nie-kolejnej wersji modelu 🙂 między [pLlamą3](https://radlab.dev/2024/08/16/pllama3-8b-70b-genai-dla-polskiego/) oraz [pLlamą3.2](https://radlab.dev/2024/10/20/pllama3-2-1b-3b-male-genai-dla-polskiego/) była też wersja pLLamy3.1 — i to o niej dzisiejszy wpis.

## Intro

Kolejna wersja modelu od Mety mówiąca lepiej po polsku! W tym wpisie przedstawiamy model [pLLama3.1](https://huggingface.co/collections/radlab/pllama31-models-6710cace79670d489fe7d9bd) w architekturze 8B. Tym razem opublikowaliśmy model *-content*, który jest mniej gadatliwą wersją modelu, model *-chat* jako bardziej rozgadana jego wersja, czysty model *-base* po LoRze, ale również udostępniliśmy *eksperymentalny model z transferem warstw adaptacyjnych* modelu pLLama3 do modelu pLLama3.1 (o tym niebawem kolejny wpis:)). Wszystkie modele dostępne oczywiście na [huggingface](https://huggingface.co/radlab) (pełna [kolekcja modeli 3.1](https://huggingface.co/collections/radlab/pllama31-models-6710cace79670d489fe7d9bd)):

- Model radlab/pLLama3.1-8B-content : to model po SFT i DPO udziela krótkich i zwięzłych odpowiedzi.
- Model radlab/pLLama3.1-8B-chat to bardziej gadatliwa wersja modelu (po SFT i DPO), idealnie nadaje się do rozmowy na czacie.
- Model radlab/pLLama3.1-8B-base-ft-16bit to model bezpośrednio po SFT z LoRa.
- Eksperymentalny model radlab/pLLama-L31-adapters-MIX-SFT-DPO z transferem warstw adaptacyjnych między modelami.

## Dataset, uczenie i wykresy

Wszystkie wersje modeli pLLamy3.1 mają jednego rodzica, mianowicie [Llama-3.1-8B-Instruct](https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct) od Meta.AI w architekturze 8B. Ten model już całkiem dobrze pisze w swojej podstawowej wersji po polsku, jednak dużo brakuje do (przynajmniej) poprawnego pisania. Stąd pomysł: douczmy i ten model 🙂

Do uczenia wykorzystaliśmy zbiór danych opracowany do wcześniejszych modeli. Krótko przypominając jest to ponad 650k instrukcji wygenerowanych automatycznie na podstawie dostępnych zbiorów danych. Każdy zbiór (np. oznaczony częściami mowy), przekształcaliśmy do postaci promtów systemowych na zasadzie pytania i odpowiedzi. W ten sposób powstał zbiór instrukcji, które wykorzystaliśmy jako dane do douczenia modelu. Do DPO również opracowaliśmy zestaw instrukcji na podstawie dostępnych korpusów językowych między innymi NKJP i KPWr.

Ze względu na ograniczenia sprzętowe SFT robiliśmy z wykorzystaniem warstw adaptacyjnych (LoRA) z kwantyzacją liczb do 16 bitów (bits and bytes). Podobnie w DPO, model bazowy ładowany był jako kwantyzowana wersja pLLamy3.1 po SFT i w trakcie DPO douczana również była warstwa adaptacyjna. Dla przypomnienia, w naszym przypadku podczas SFT przekrzywiamy wagi modelu w stronę języka polskiego, zaś w procesie DPO uczymy model poprawnego generowania tekstu — pod względem gramatycznym i interpunkcyjnym. Modele trenowaliśmy na pojedynczych kartach graficznych RTX 4090 (24 GB). SFT (LoRA) trwało 14d 2h 3m 52s. Zaś DPO 2d 15h 2m 42s. Różnica między modelem *-content* a *-chat* to kwestia innego sposobu łączenia warstwy adaptacyjnej z modelem (ale o tym będzie osobny wpis). Poniżej dwa wykresy, pierwszy z nich to wartość funkcji straty w SFT, drugi to wartości logitów *chosen* i *rejected* podczas DPO.

Funkcja straty podczas SFT z Lorą

![](@media/pllama3-1-8b-czyli-srednio-duze-a-nawet-male-genai-dla-polskiego/03-image-1.avif)

I proces DPO:

![](@media/pllama3-1-8b-czyli-srednio-duze-a-nawet-male-genai-dla-polskiego/04-image.avif)

## Outro

Czym różni się model w wersji 3.1 od modelu [pLLama3](https://radlab.dev/2024/08/16/pllama3-8b-70b-genai-dla-polskiego/)? Przede wszystkim wielkością kontekstu. Model pLLama3 miał ograniczony kontekst do 8k tokenów. Wersja pLLamy3.1 to kontekst o długości 128k tokenów (to wynika z modelu bazowego, czyli w pLLamie 3 douczaliśmy Llamę3 od Mety, zaś w pLLamie3.1 model LLama3.1 od mety). W testach w RAGu pLLama3.1 działa zdecydowanie lepiej od wersji 3 przede wszystkim ze względu na większy kontekst. W tej chwili podczas odpowiadania na pytanie model jest w stanie pomieścić dużo więcej informacji, co mocno zmniejsza częstotliwość jego odpytywania, redukuje mocno problem ze zbyt częstym odpytywaniem modelu, dzieleniem danych do wielkości wejścia (przy okazji redukuje problem składania odpowiedzi końcowej w RAG na podstawie cząstkowych odpowiedzi przy małym kontekście).

A jako dodatek na HF model, który nazwaliśmy L31 ([pLLama-L31-adapters-MIX-SFT-DPO](https://huggingface.co/radlab/pLLama-L31-adapters-MIX-SFT-DPO)) jako pewien eksperyment przy mixowaniu modeli.

Tyle na dziś, dzięki!
