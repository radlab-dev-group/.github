---
title: "pLlama3.2 (1B + 3B) – małe GenAI dla polskiego"
date: 2024-10-20
slug: pllama3-2-1b-3b-male-genai-dla-polskiego
description: "pLLama – wygenerowane za pomocą AI Intro Cześć Wam! Dziś bardzo krótki wpis. Wpis o modelu, niewielkim jak na te czasy. Pewnie słyszeliście o LLamie3.2 od…"
tags: ["dpo", "fine-tuning", "genai", "hf", "huggingface", "pllama", "transformers", "uczenie"]
categories: ["eksperyment", "GenAI", "huggingface", "llama", "model", "transformatory"]
image: media/pllama3-2-1b-3b-male-genai-dla-polskiego/_featured.png
lang: pl
wp_id: 2658
---

![pLLama - wygenerowane za pomocą AI](@media/pllama3-8b-70b-genai-dla-polskiego/01-image.png)

*pLLama – wygenerowane za pomocą AI*

## Intro

Cześć Wam!

Dziś bardzo krótki wpis. Wpis o modelu, niewielkim jak na te czasy. Pewnie słyszeliście o LLamie3.2 od MetaAI? Meta udostępniła ostatnio modele do generowania treści (*Instruct*) ale i obrazów (*Vision-Instruct*).

![](@media/pllama3-2-1b-3b-male-genai-dla-polskiego/02-image.avif)

![](@media/pllama3-2-1b-3b-male-genai-dla-polskiego/03-image-1.avif)

Niestety modele *Vision-Instruct* nie są dostępne w Unii Europejskiej no i przy okazji w naszym kraju.

![](@media/pllama3-2-1b-3b-male-genai-dla-polskiego/04-image-2.avif)

Zatem…. co nam zostało? Zostało nam douczyć małe modele tekstowe w architekturze 1B oraz 3B na nasz język 😉

## Dane i Trening

Do douczania zastosowaliśmy najpierw technikę fine-tuningu, a następnie w procesie DPO trenowaliśmy oba modele na korekcję języka. Dane dokładnie te same, co w przypadku pLLamy3 ([Kliknij aby przeczytać artykuł](https://radlab.dev/2024/08/16/pllama3-8b-70b-genai-dla-polskiego/)) .Zarówno do fine-tuningu, jak i DPO. Jedynie mała zmiana w hiperparametrach uczenia (batch size, learning rate). Liczba epok w FT to 5, liczba kroków w DPO 50k. A… no i uczenie na 16 bitach 🙂

Zobaczcie sami na wykres funkcji straty zarówno na części treningowej i ewaluacyjnej (to sam proces fine-tuningu na język polski):

![](@media/pllama3-2-1b-3b-male-genai-dla-polskiego/05-image-3.avif)

![](@media/pllama3-2-1b-3b-male-genai-dla-polskiego/06-image-4.avif)

I dokładnie taka między nimi jest różnica 🙂

## Odczucia

Jako, że modele 1B oraz 3B to destylacja modeli już istniejących zapewne oceniana w większości na danych anglojęzycznych, ciekawy był efekt całego procesu douczania tych modeli. Model w architekturze 1B (zarówno po FT ale i po DPO) to chyba najmniej sprawny model z całej naszej kolekcji — ale statystyki mety pokazują dokładnie to samo. Zaś model w architekturze 3B, to zupełnie inna liga niż 1B. Można powiedzieć, że działa zgodnie z oczekiwaniami 🙂

Porównywanie ich do większych modeli mija się trochę z celem, ponieważ w przypadku 1B i 3B Meta postawiła na możliwość uruchamiania ich na mniej wydajnym sprzęcie, a nawet na komórce 😉 O ile model 1B słabo sobie radzi, o tyle 3B potrafi zaskoczyć.

## Modele do pobrania

Zapraszamy oczywiście na nasz HuggingFace, na którym stworzyliśmy kolekcję z modelami *[pLLama3.2 Models](https://huggingface.co/collections/radlab/pllama32-models-6710bdf9eac198072676a52f)*. Wszystkie modele oczywiście udostępniamy publicznie za darmo:

- Modele w architekturze 1B: radlab/pLLama3.2-1B – model tylko po fine-tuningu, oraz radlab/pLLama3.2-1B-DPO po FT + DPO
- Modele w architekturze 3B: radlab/pLLama3.2-3B model tylko po fine-tuning, oraz radlab/pLLama3.2-3B-DPO po FT + DPO

Częstujcie się 🙂

## **Co dalej?**

> Dalej będzie nie-ko-po-le-i: pLLama3.1-8B (to ten zielony wykres) oraz L31 jako pewien ciekawy mix…

![](@media/pllama3-2-1b-3b-male-genai-dla-polskiego/07-image-5.avif)

![](@media/pllama3-2-1b-3b-male-genai-dla-polskiego/08-image-6.avif)
