---
title: "Bi-encoder and cross-encoder model"
date: 2024-04-30
updated: 2025-09-26
slug: dwa-nowe-modele-encoderow-dla-polskiego
description: "The possibilities offered by generative models are enormous, as evidenced by the success of OpenAI and its flagship product, ChatGPT. Generative models based…"
categories: ["embedding", "huggingface", "models", "transformers"]
image: media/_featured.png
lang: en
translation_of: dwa-nowe-modele-encoderow-dla-polskiego
wp_id: 2148
---

The possibilities offered by generative models are enormous, as evidenced by the success of [OpenAI](https://openai.com/)  and its flagship product, [ChatGPT](https://chat.openai.com). Generative models based on transformer architecture are on par with humans in terms of content creation, whether in the form of text, images, or more complex animations. Despite their powerful *generative* capabilities, they have one fundamental drawback: updating information in these models. When querying such a model for information from the everyday world that goes beyond the training set, it is virtually impossible for the model to provide the correct answer. One solution to this problem is an approach based on Retrieval Augmented Generation (RAG).

### Retrieval Augmented Generation

The idea behind RAG is to separate the i*nformation layer* from the generative model. The information layer is a form of database where information is stored, while the generative model is used to provide answers based on information retrieved from the database. What does this approach offer? A lot. 😉

It introduces a breakthrough in NLP, where the previously used Retrieval Information approaches (replaced by new mechanisms), combined with well-functioning generative models, are able to provide the latest information. Since this information is stored in a database, it can be updated on an ongoing basis. When a piece of information becomes outdated, it can simply be *removed* from the database. As a result, when providing an answer, the generative model will not receive this information as context for its response, which will limit the model’s hallucinations.

### Machinery

So what is needed to implement the RAG approach? In the simplest case, it is a few mechanisms:

- a mechanism that convert text into vector form (hereinafter referred to as an embedder);
- a database that allows indexed texts to be stored and searched (e.g., Milvus );
- a generative model that will provide answers based on the context provided (e.g., LLama3 from MetaAI ).

In more complex cases, not only the information retrieval process is controlled, but also the collection of texts returned by the search engine.

### Embedder and reranker model

In today’s post, we would like to present our two models. The first one is an *[embedder](https://huggingface.co/radlab/polish-bi-encoder-mean)*, that can be used to transform text into vector form. The second one is a mechanism that *[reranking](https://huggingface.co/radlab/polish-cross-encoder)* the results returned by a semantic search engine. The technical difference between an *embedder* (bi-encoder) and a *reranker* (cross-encoder) is very well presented in [this article](https://sbert.net/examples/applications/cross-encoder/README.html). In a nutshell: we train the bi-encoder model on a semantic similarity process, where the evaluation function is the indicated semantic distance, in our case the cosine angle measure. In the case of a cross-encoder, the model is trained on the value of the loss function, resulting from the correlation of the model’s responses to the test set.

We used the [sentence-transformers](https://sbert.net/) library to build these models. The loss function for the bi-encoder model is the cosine distance, and for the cross-encoder it is [CECorrelationEvaluator](https://github.com/yym6472/ConSERT/blob/master/sentence_transformers/cross_encoder/evaluation/CECorrelationEvaluator.py). As a dataset, we used existing information retrieval datasets, e.g.,  [ipipan/maupqa](https://huggingface.co/datasets/ipipan/maupqa), which we enriched with our [radlab/polish-sts-dataset](https://huggingface.co/datasets/radlab/polish-sts-dataset). Of course, in both cases, these datasets had to be transformed accordingly and adapted to the problem of training the bi-encoder and cross-encoder.

#### “bi-encoder”

The bi-encoder model trained for 1 day and 9 hours on a single NVIDIA GeForce RTX 4090 card. The Pearson and Spearman correlation values, measured on the evaluation set, are as follows:

![](media/01-image.png)

What is most interesting from our perspective is the correlation for *Cosine-Similariy*. The correlation values are high, and in both cases, they can be interpreted as a strong and fairly strong correlation. This means that the model’s responses strongly correlate with the test data. The published bi-encoder model has an averaged pooling layer. It can be used to create embeddings from text and compare them semantically. Link to the model on huggigface: [radlab/polish-bi-encoder-mean](https://huggingface.co/radlab/polish-bi-encoder-mean).

Sample code to load the model using sentence-transformers, which will create a vector representation for the specified texts:

```python
from sentence_transformers import SentenceTransformer
sentences = ['Ala ma kota i psa, widzi dzisiaj też śnieg', 'Ewa ma białe zęby']

model = SentenceTransformer('radlab/polish-bi-encoder-mean')
embeddings = model.encode(sentences)
print(embeddings)
```

#### “cross-encoder”

We have also made available a *cross-encoder* model that returns the relevance value of two texts. It can, of course, be used as a *reranker*, e.g., in a semantic search engine. What might such a process look like? As usual- it’s simple 🙂

As a result of a semantic search, we get a set of texts that are ranked according to the similarity of one text fragment to another – the one being searched for. This set is the perfect input for a model whose goal is not only to determine the similarity between two text fragments, but also to determine which fragment better matches the searched text.

We have also made the finished reranking model available on huggingface in the [radlab/polish-cross-encoder](https://huggingface.co/radlab/polish-cross-encoder) repository. This model was trained on a single NVIDIA GeForce RTX 4090 card for 3 days and 10 hours. Pearson and Spearman correlation on the test set:

- Pearson Correlation : 0.9360742942528038
- Spearman Correlation : 0.8718174291678207

The values of both correlations, as in the case of the bi-encoder, are interpreted as a strong and fairly strong correlation between the model’s responses and the test set.

Sample code (using sentence-transformers) that assigns responses to questions:

```json
from sentence_transformers.cross_encoder import CrossEncoder

model_path = "radlab/polish-cross-encoder"
model = CrossEncoder(model_path)

questions = [
    "Jaką mamy dziś pogodę? bo Andrzej nic nie mówił.",
    "Gdzie jedzie Andrzej? Bo wczoraj był w Warszawie.",
    "Czy oskarżony się zgadza z przedstawionym wyrokiem?",
]
answers = [
    "Pan Andrzej siedzi w pociągu i jedzie do Wiednia. Ogląda na telefonie zabawne filmiki.",
    "Poada deszcz i jest wilgotno, jednak wczoraj było słonecznie.",
    "Wyrok jest prawomocny i nie podlega dalszym rozważaniom.",
]
for question in questions:
    context_with_question = [(s, question) for s in answers]
    results = sorted(
        {
            idx: r for idx, r in enumerate(model.predict(context_with_question))
        }.items(),
        key=lambda x: x[1],
        reverse=True,
    )

    print(f"QUESTION: {question}")
    print("ANSWERS (sorted):")
    for idx, score in results:
        print(f"\t[{score}]\t{answers[idx]}")
    print("")
```

The result of calling the above code should be similar to:

```json
QUESTION: Jaką mamy dziś pogodę? bo Andrzej nic nie mówił.
ANSWERS (sorted):
        [0.016749681904911995]  Poada deszcz i jest wilgotno, jednak wczoraj było słonecznie.
        [0.01602918468415737]   Pan Andrzej siedzi w pociągu i jedzie do Wiednia. Ogląda na telefonie zabawne filmiki.
        [0.016013670712709427]  Wyrok jest prawomocny i nie podlega dalszym rozważaniom.

QUESTION: Gdzie jedzie Andrzej? Bo wczoraj był w Warszawie.
ANSWERS (sorted):
        [0.5997582674026489]    Pan Andrzej siedzi w pociągu i jedzie do Wiednia. Ogląda na telefonie zabawne filmiki.
        [0.4528200924396515]    Wyrok jest prawomocny i nie podlega dalszym rozważaniom.
        [0.17350871860980988]   Poada deszcz i jest wilgotno, jednak wczoraj było słonecznie.

QUESTION: Czy oskarżony się zgadza z przedstawionym wyrokiem?
ANSWERS (sorted):
        [0.8431766629219055]    Wyrok jest prawomocny i nie podlega dalszym rozważaniom.
        [0.6823258996009827]    Poada deszcz i jest wilgotno, jednak wczoraj było słonecznie.
        [0.558414101600647]     Pan Andrzej siedzi w pociągu i jedzie do Wiednia. Ogląda na telefonie zabawne filmiki.
```

### Outro

Both models presented today can be easily used to build a system based on the RAG approach. They can also be used as independently operating models. However, it is worth noting that the performance measured by the cross-encoder model’s operating time is incomparably lower than that of the bi-encoder model. Therefore, in the final solution, it is recommended to combine both models into a single pipeline. In the first step, based on text embeddings, the most similar fragments are searched for in the database, and then the question is matched to a limited set of answers based on the returned fragments.

Of course, for more models, visit our [huggingface](https://huggingface.co/radlab).

## Unlock the potential of your data with our ML/NLP. Bon appetit! 😉
