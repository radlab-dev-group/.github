---
title: "Llm-Router- a connector between an application and generative models"
date: 2025-10-23
updated: 2025-10-24
slug: llm-router-a-connector-between-an-application-and-generative-models
description: "This time, we’re introducing a project that we’ve been using internally for a while. Given its high versatility, it might be useful to others as well. We…"
categories: ["embedding", "experiment", "GenAI", "github", "MachineLearning", "method", "models", "repository"]
image: media/_featured.jpeg
lang: en
translation_of: llm-router
wp_id: 4142
---

This time, we’re introducing a project that we’ve been using internally for a while. Given its high versatility, it might be useful to others as well. We encourage you to try it out and report any issues you encounter 🙂

![](media/01-llm-router-blog.png)

In the following part, we’ll briefly describe the contents of the repository, how to run the ready-made image (yes, just download and run :)), and an example configuration. In the [README](https://github.com/radlab-dev-group/llm-router/blob/main/README.md) on [Github](https://github.com/radlab-dev-group), we covered the project from a technical angle; here, we’re focusing more on usage.

## Login

We’ve publicly shared the llm-router project on [GitHub](https://github.com/radlab-dev-group/llm-router). This solution works like a router in the networking world, with one key difference: routing in **llm-router happens between the user** and **generative models**. Just as a router receives a message, processes it, knows where to forward it, and sends a response back to the user, our llm-router receives a query from the user specifying which model they’d like to use. It then routes the query to the appropriate model (it knows their locations), processes the model’s output, and returns the final response to the user. In short, the user doesn’t need to worry about where a model is running—they just need to know the model’s name and send the query to llm-router.

## Supernova explosion

What can llm-router be used for? It’s a solution available via a REST API that manages traffic between an application and a generative model. It does this in such a way that the user/**application doesn’t need** to know the **model’s location,** connection parameters, and, more importantly, **doesn’t store private keys** for external generative model services (like OpenAI or Google). This is because all the model handling logic resides on the llm-router side. You just need to connect a list of external models to it, and the router will take care of the appropriate routing. It doesn’t matter whether the model is running locally, for instance using VLLM, LMStudio, or Ollama, or if it’s publicly available in the cloud.

Currently, all APIs that implement the Ollama or OpenAI standard are supported. Moreover, the router can **handle traffic between different standards** (including streaming). Even if a user has been using Ollama so far, they can stick with that standard and, without modifying their application code, use llm-router to send a query to an API like VLLM. This greatly simplifies deploying models in production.

Additionally, the **predefined endpoints** ([click](https://github.com/radlab-dev-group/llm-router?tab=readme-ov-file#%EF%B8%8F-endpoints-overview)), which can be freely **extended and new ones added**, **significantly streamline** the software **development proces**s. The same functionality that would have to be coded into the application (and would only be available there) can now be implemented on the llm-router side, as a **central access node**. This simplifies introducing fixes, new features, and managing them. These dedicated endpoints can be thought of as **agents performing** specific **functions.**

**Configuration flexibility** also allows for **naming models arbitrarily**. For example, from the application’s perspective, the model it queries might be named `model_generatywny`, and this name is then resolved to the correct model and host by the llm-router (the recording below shows an example of how this can work – **the application doesn’t know which model it’s running**).

## **A box of building blocks**

And inside the box, there are two smaller boxes: one with an assembled toy and the other with actual building blocks. Let’s start with the toy, which is a publicly available image on **[quay](https://quay.io/organization/radlab)** that can be downloaded and run without building. We only need to configure the models we have access to or are currently using. The process of downloading and running the image is very simple: just have Docker installed on your system and download the ready-made image from our Quay repository. To download the image, just run:

```bash
docker run -p 5555:8080 quay.io/radlab/llm-router:rc1
```

and update to the latest version:

```bash
docker pull quay.io/radlab/llm-router:rc1
```

After downloading, t**he image will run automatically** and expose the llm-router **API** in its simplest Flask-based version on port 5555. The flag `-p 5555:8080` means we’re forwarding port 8080 from inside the Docker container (where the router runs) to port 5555, accessible externally. The base server is Flask, so before scaling up (especially for streaming), we recommend reviewing [ ](https://github.com/radlab-dev-group/llm-router?tab=readme-ov-file#3%EF%B8%8F%E2%83%A3-optional-configuration-via-environment)**[configuration via environment variables ](https://github.com/radlab-dev-group/llm-router?tab=readme-ov-file#3%EF%B8%8F%E2%83%A3-optional-configuration-via-environment)** and considering deployment with Gunicorn (with a set worker count, log level, etc.). To run llm-router with a custom config, simply mount it into the image to override the default config located at `/srv/llm-router/resources/configs/models-config.json`. Pass the `-v` parameter to Docker like this:

```text
-v sciezka/do/lokalnego/pliku/models.json:/srv/llm-router/resources/configs/models-config.json
```

Now, the building blocks… The instructions are available in the [README](https://github.com/radlab-dev-group/llm-router/blob/main/README.md) (along with a [Polish](https://github.com/radlab-dev-group/llm-router/blob/main/llm_router_api/endpoints/README-pl.md) description featuring an example advanced endpoint you can add to llm-router yourself), so we won’t repeat that here. However, the key takeaway is how the configuration file is structured. Below, in “Something for the eye,” we’ve included a sample JSON configuration for three models:

- google/vllm : This is the google/gemma-3-12b-it model running on the local network ( http://192.168.100.79:7000/ ), launched via VLLM.
- google/chmura : This is actually the gemini-2.5-flash-lite model accessible through Google’s cloud API https://generativelanguage.googleapis.com/v1beta/openai , for which you’ll need to insert your API key ( PUT YOUR API KEY HERE ).
- openai/model : This is the gpt-oss:120b model running on the local network [http://192.168.100.66:11434](http://192.168.100.66:11434) , launched via Ollama.

## Something for the Eyes

The video below contains several screens: the *top left corner* shows a view of VLLM with google/gemma3-12b-it, the *bottom left corner* shows Ollama with the gpt-oss:120b model, the *bottom right corner* is a console with the running llm-router, and the *top right corner* is the [AI Assistant](https://www.jetbrains.com/ai/) plugin for PyCharm. By default, the plugin allows connecting to one model provider, whereas connecting the llm-router allows injecting any standard, even one not natively supported by the application. Additionally, the video shows how you can change model names so that the application side doesn’t know which model is underneath. Meanwhile, in the console at the bottom, you can see how the llm-router receives requests and routes them to the appropriate host:

{{< video media/pycharm-llm-router.webm >}}

The configuration used to start Llm-Router:

```json
{
  "google_models": {
    "google/vllm": {
      "api_host": "http://192.168.100.79:7000/",
      "api_token": "",
      "api_type": "vllm",
      "input_size": 4096,
      "model_path": "google/gemma-3-12b-it"
    },
    "google/chmura": {
      "api_host": "https://generativelanguage.googleapis.com/v1beta/openai/",
      "api_token": "PUT YOUR API KEY HERE",
      "api_type": "openai",
      "input_size": 512000,
      "model_path": "gemini-2.5-flash-lite"
    }
  },
  "openai_models": {
    "openai/model": {
      "api_host": "http://192.168.100.66:11434",
      "api_token": "",
      "api_type": "ollama",
      "input_size": 256000,
      "model_path": "gpt-oss:120b"
    }
  },
  "active_models": {
    "google_models": [
      "google/vllm",
      "google/chmura"
    ],
    "openai_models": [
      "openai/model"
    ]
  }
}
```

And the full script with Docker startup (what is run in the terminal in the video — i.e., full configuration and change of all default parameters :)):

```bash
#!/bin/bash

PWD=$(pwd)

docker run \
  -p 5555:8080 \
  -e LLM_ROUTER_TIMEOUT=500 \
  -e LLM_ROUTER_IN_DEBUG=1 \
  -e LLM_ROUTER_MINIMUM=1 \
  -e LLM_ROUTER_EP_PREFIX="/api" \
  -e LLM_ROUTER_SERVER_TYPE=gunicorn \
  -e LLM_ROUTER_SERVER_PORT=8080 \
  -e LLM_ROUTER_SERVER_WORKERS_COUNT=4 \
  -e LLM_ROUTER_DEFAULT_EP_LANGUAGE="pl" \
  -e LLM_ROUTER_LOG_FILENAME="llm-proxy-rest.log" \
  -e LLM_ROUTER_EXTERNAL_TIMEOUT=300 \
  -e LLM_ROUTER_MODELS_CONFIG=/srv/cfg.json \
  -e LLM_ROUTER_PROMPTS_DIR="/srv/prompts" \
  -v "${PWD}/resources/configs/models-config-names.json":/srv/cfg.json \
  -v "${PWD}/resources/prompts":/srv/prompts \
  quay.io/radlab/llm-router:rc1
```

## Logout

One of the places where Llm-Router is running is our playground.

Every generative model functionality is programmed as a dedicated endpoint in llm-router. We’re sharing the code under the Apache 2.0 license—so you can use it commercially and non-commercially. Enjoy! 😊

We encourage you to try it out and share your suggestions and feedback.

> **Update (v1.1+ Release):** The planned features (6 advanced Load Balancing strategies, Redis-backed sliding-window Rate Limiting, Prometheus metrics, and the PII / NASK & Sójka guardrail plugin pipeline) are now fully available! Explore the [full LLM Router product page](/en/products/llm-router/).
