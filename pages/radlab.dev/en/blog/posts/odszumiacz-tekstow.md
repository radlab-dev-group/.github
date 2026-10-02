---
title: "Text denoiser"
date: 2024-04-20
updated: 2025-09-24
slug: odszumiacz-tekstow
description: "Currently, the world of natural language processing is dominated by solutions based on transformer architecture models. The diversity of these models has…"
categories: ["huggingface", "models", "t5", "transformers"]
image: media/odszumiacz-tekstow/_featured.png
lang: en
translation_of: odszumiacz-tekstow
wp_id: 2195
---

Currently, the world of natural language processing is dominated by solutions based on *transformer* architecture models. The diversity of these models has practically dominated every area of NLP. Regardless of their architecture and purpose, however, they have one thing in common: a high demand for good-quality data, which is used to train these models.

## The problem to be solved

So where can the data be obtained? Of course, it depends on the specific case and purpose of the model. And data, as data, is often stored in various formats, including one of the least accessible for automatic processing, namely *pdf*. The concept of saving in *pdf* format is primarily to present the saved content so that the graphic form is the same in any reader on any device. However, when automatically processing these files, problems with reading the content may be encountered.

An example of a problem with text that occurs after reading a poor-quality *pdf* file:

```text
Strona...Tytuł...%6%z%50%|.....Zdecydowana0większość0czerwonych.karłów$należy#do,typu,widmowego%M,%ale%zalicza^się^do^nich^także^wieleHgwiazdHpóźnychHpodtypówHtypuHwidmowegoHKHorazHrzadkoHwystępujące,,najsłabsze,gwiazdy,typu,L.,Maksimum%intensywności%emitowanego%światła%przypada%w%zakresie%światła%czerwonego%lub%nawet%bliskiej%podczerwieni.
```

The correct form of this text is:

```text
Zdecydowana większość czerwonych karłów należy do typu widmowego M, ale zalicza się do nich także wiele gwiazd późnych podtypów typu widmowego K oraz rzadko występujące, najsłabsze gwiazdy typu L. Maksimum intensywności emitowanego światła przypada w zakresie światła czerwonego lub nawet bliskiej podczerwieni.
```

## Solution to the problem

Seeing many problems that are repetitive on a large scale, we developed a method of noise generator to data that resembles the problems encountered.The method is based on conditional probabilities and maps the distribution of problems from mass-processed texts. The developed collection contains 1 M texts, from which we randomly selected 100K for the *noise removal* model training process.

## Training the noise remover

We used a pre-trained base model in the T5 [allegro/plt5-base](https://huggingface.co/allegro/plt5-base) architecture, which we trained on the data cleaning problem. Training the model took 5 hours and 30 minutes on a single NVIDIA GeForce RTX 4090 card. *Loss function* graph for the evaluation set:

![](@media/odszumiacz-tekstow/01-image.png)

## Example of operation

We have made the trained model available on our [huggingface](https://huggingface.co/radlab) repository [radlab/polish-denoiser-t5-base](https://huggingface.co/radlab/polish-denoiser-t5-base).

The input to the model is text in the form: `denoise: <text to noise remover>.` For the example above, it is:

```text
denoise: Strona...Tytuł...%6%z%50%|.....Zdecydowana0większość0czerwonych.karłów$należy#do,typu,widmowego%M,%ale%zalicza^się^do^nich^także^wieleHgwiazdHpóźnychHpodtypówHtypuHwidmowegoHKHorazHrzadkoHwystępujące,,najsłabsze,gwiazdy,typu,L.,Maksimum%intensywności%emitowanego%światła%przypada%w%zakresie%światła%czerwonego%lub%nawet%bliskiej%podczerwieni.
```

The output from the model looks like this:

```text
Zdecydowana większość czerwonych karłów należy do typu widmowego M, ale zalicza się do nich także wiele gwiazd późnych podtypów typu widmowego K oraz rzadko występujące, najsławsze gwiazdy typu L. Maksimum intensywności emitowanego światła przypada w zakresie światła czerwonego lub nawet bliskiej podczerwieni.
```

Sample code that allows you to run the model for the text from the example above:

```python
from transformers import T5ForConditionalGeneration, T5Tokenizer

def do_inference(text, model, tokenizer):
    input_text = f"denoise: {text}"
    inputs = tokenizer.encode(
        input_text,
        return_tensors="pt",
        max_length=256,
        padding="max_length",
        truncation=True,
    )

    corrected_ids = model.generate(
        inputs,
        max_length=256,
        num_beams=5,
        early_stopping=True,
    )

    corrected_sentence = tokenizer.decode(corrected_ids[0], skip_special_tokens=True)
    return corrected_sentence

model = T5ForConditionalGeneration.from_pretrained("radlab/polish-denoiser-t5-base")
tokenizer = T5Tokenizer.from_pretrained("radlab/polish-denoiser-t5-base")

text_str = "Strona...Tytuł...%6%z%50%|.....Zdecydowana0większość0czerwonych.karłów$należy#do,typu,widmowego%M,%ale%zalicza^się^do^nich^także^wieleHgwiazdHpóźnychHpodtypówHtypuHwidmowegoHKHorazHrzadkoHwystępujące,,najsłabsze,gwiazdy,typu,L.,Maksimum%intensywności%emitowanego%światła%przypada%w%zakresie%światła%czerwonego%lub%nawet%bliskiej%podczerwieni."

print(do_inference(text_str, model, tokenizer))
```

Feel free to use it, bon appétit 🙂

---

> **Prompt Sanitization & Security:** For production-grade personal data anonymization and masking before inference, explore [PII Masker](/en/products/pii-masker/) and the [LLM Router](/en/products/llm-router/) gateway.
