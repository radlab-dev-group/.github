---
title: "Llm-Router – łącznik między aplikacją, a modelami generatywnymi"
date: 2025-10-13
updated: 2025-10-23
slug: llm-router
description: "Tym razem przybywamy z projektem, który wykorzystujemy od jakiegoś czasu wewnętrznie. Jednak ze względu na dość dużą uniwersalność rozwiązania — może komuś się…"
tags: ["huggingface", "llm", "open-source", "transformers"]
categories: ["GenAI", "github", "model", "narzędzia", "open-source", "repozytorium", "transformatory"]
image: media/llm-router/_featured.avif
lang: pl
wp_id: 4074
---

Tym razem przybywamy z projektem, który wykorzystujemy od jakiegoś czasu wewnętrznie. Jednak ze względu na dość dużą uniwersalność rozwiązania — może komuś się przydać — a nawet zachęcamy do korzystania i zgłaszania problemów 🙂

![](@media/llm-router/01-llm-router-blog.avif)

W dalszej części krótko opiszemy zawartość repozytorium, sposób uruchomienia gotowego obrazu (tak, wystarczy pobrać i uruchomić :)) oraz przykład konfiguracji. W [README](https://github.com/radlab-dev-group/llm-router/blob/main/README.md) na [githubie](https://github.com/radlab-dev-group) opisaliśmy projekt od strony technicznej, tutaj skupiamy się bardziej na wykorzystaniu.

## Login

Na [githubie](https://github.com/radlab-dev-group/llm-router) udostępniliśmy publicznie projekt llm-router. To rozwiązanie, które działa jak router w świecie sieciowym z tą różnicą, że routing w **llm-router** jest **między użytkownikiem**, **a modelami generatywnymi**. Tak jak router dostaje wiadomość, obsługuje ją, wie gdzie ją skierować dalej i odsyła do użytkownika odpowiedź, tak nasz llm-router otrzymuje zapytanie od użytkownika z informacją o modelu z jakiego chce skorzystać, i już llm-router odpowiednio przekierowuje zapytanie do modelu (zna ich lokalizacje), obsługuje wynik modelu i zwraca odpowiedź do użytkownika. Innymi słowy – użytkownik nie martwi się gdzie jakiś model jest uruchomiony, a jedynie musi znać nazwę modelu i skierować zapytanie do llm-routera.

## Eksplozja supernowej

Do czego można wykorzystać llm-router? To rozwiązanie dostępne poprzez API RESTowe, które obsługuje ruch między aplikacją a modelem generatywnym. Robi to w taki sposób, że użytkownik/**aplikacja** **nie** musi **znać** **lokalizacji** **modelu**, parametrów połączenia, a tym bardziej **nie** **przechowuje** **kluczy** **prywatnych** do zewnętrznych serwisów z modelami generatywnymi (openai, google), bo cała logika obsługi modelu jest po stronie llm-routera. Wystarczy wpiąć do niego listę zewnętrznych modeli, a już router zadba o odpowiednie przekierowywanie. I tutaj nie ma znaczenia czy model jest lokalnie uruchomiony np. za pomocą VLLM, LMStudio czy Ollamy, czy też jest dostępny publicznie w chmurze.

Aktualnie obsługiwane są wszystkie API, które implementują standard Ollama lub OpenAI, a mało tego router potrafi **przekierować** **ruch** między **różnymi** **standardami** (również strumieniowanie). Nawet jeżeli do tej pory użytkownik korzystał z Ollamy nadal może pozostać przy tym standardzie i **bez modyfikacji kodu aplikacji**, ale za pomocą llm-routera może wysłać zapytanie do API np. VLLM co daje duże uproszczenie w produkcyjnym uruchamianiu modeli.

Dodatkowo, **predefiniowane** **endpointy** ([klik](https://github.com/radlab-dev-group/llm-router?tab=readme-ov-file#%EF%B8%8F-endpoints-overview)), które dowolnie można **rozbudowywać** i **dodawać** **nowe**, znacznie **upraszczają** proces **wytwarzania** **oprogramowania**. Ta sama funkcjonalność, która musiałaby być oprogramowana w aplikacji (i **dostępna** by była tylko w niej), teraz może być zaimplementowana po stronie llm-routera, jako **centralnym** **węźle** dostępowym. Upraszcza to wprowadzanie poprawek, nowych funkcjonalności i zarządzenie nimi. Dedykowane endpointy, można nazwać **agentami** **realizującymi** określone **funkcjonalności**.

**Elastyczność** **konfiguracji**, daje również możliwość **nazywania** **modeli** **dowolnie**, np. po stronie aplikacji model, do którego aplikacja wysyła zapytanie może się **np**. nazywać `model_generatywny`, a ta nazwa rozwiązywana jest do poprawnego modelu i hosta po stronie llm-routera (na nagraniu poniżej przykład jak to może wyglądać – **aplikacja** **nie wie** **jaki** **model** **uruchamia**).

## Karton z klockami

A w kartonie w dwa kartony: jeden ze złożoną zabawką a drugi faktycznie z klockami. Zacznijmy od **zabawki**, czyli **publicznie** dostępnego **[obrazu na quay](https://quay.io/organization/radlab),** który można pobrać i uruchomić **bez** **budowania**. Jedynie **konfigurujemy** **modele**, do których mamy dostęp/aktualnie wykorzystujemy. **Proces** pobrania i **uruchomienia** obrazu **jest** bardzo **prosty**, wystarczy posiadać zainstalowanego w systemie dockera i pobrać gotowy obraz z naszego repozytorium [Quay](https://quay.io/organization/radlab). Do pobrania obrazu **wystarczy**:

```bash
docker run -p 5555:8080 quay.io/radlab/llm-router:rc1
```

a do **aktualizacji** do najnowszej wersji:

```bash
docker pull quay.io/radlab/llm-router:rc1
```

Po pobraniu, **obraz** **sam się** **uruchomi** i wystawi **api** <em>llm-routera</em> w najprostszej wersji z Flaskiem na porcie 5555 (`-p 5555:8080` oznacza, że przekierowujemy port *8080* z wewnątrz dockera, na którym działa router, na port *5555* dostępny na zewnątrz dockera). Serwerem podstawowym jest Flask, dlatego przed wykorzystywaniem na większą skalę (szczególnie z opcją strumieniowania), zachęcamy do **przeczytania** [możliwości **konfiguracji** zmiennymi środowiskowymi](https://github.com/radlab-dev-group/llm-router?tab=readme-ov-file#3%EF%B8%8F%E2%83%A3-optional-configuration-via-environment) – i rozważenie uruchomienia z **gunicornem** z ustaloną liczba **workerów**, log-levelem itp. Aby uruchomić llm-router z własnych konfigiem, wystarczy podmontować go do obrazu i podmienić domyślny, który znajduje się w obrazie pod ścieżką `/srv/llm-router/resources/configs/models-config.json`. Czyli przekazujemy parametr `-v` do dockera:

```text
-v sciezka/do/lokalnego/pliku/models.json:/srv/llm-router/resources/configs/models-config.json
```

Teraz klocki… instrukcja dostępna w [README](https://github.com/radlab-dev-group/llm-router/blob/main/README.md) (oraz [opis po polsku z przykładowym zaawansowany endpointem](https://github.com/radlab-dev-group/llm-router/blob/main/llm_router_api/endpoints/README-pl.md), który samemu można dodać do *llm-routera*), dlatego tutaj nie będziemy tego powtarzać, jednak to co jest kluczowe, to sposób budowy pliku konfiguracyjnego. Poniżej w „Coś dla oka” zamieściliśmy przykładowy plik json, z konfiguracją do trzech modeli:

- google/vllm – to model google/gemma-3-12b-it uruchomiony w sieci lokalnej ( http://192.168.100.79:7000/ ), uruchomiony za pomocą VLLMa;
- google/chmura – to tak na prawdę model gemini-2.5-flash-lite dostępny przez api chmurowe googla: https://generativelanguage.googleapis.com/v1beta/openai/ do którego posiadamy klucz PUT YOUR API KEY HERE ;
- openai/model – to model gpt-oss:120b dostępny w lokalnej sieci na hoście http://192.168.100.66:11434 uruchomiony za pomocą Ollamy;

## Coś dla oka

Filmik poniżej zawiera kilka ekranów: lewy górny róg, to podgląd na VLLMa z google/gemma3-12b-it, dolny lewy róg, to Ollama z modelem `gpt-oss:120b`, dolny prawy róg – konsola z uruchomionym llm-routerem, zaś prawy górny róg to wtyczka[ AI Assistant ](https://www.jetbrains.com/ai/)do *Pycharma*. Domślnie wtyczka umożliwia podpięcie się do jednego providera modeli, zaś wpięcie llm-routera pozwala wstrzyknąć dowolny standard, nawet ten nieobsługiwany przez aplikację. Dodatkowo na filmiku pokazaliśmy jak można zmienić nazwy modeli, aby od strony aplikacji nie było wiadomo jaki model jest pod spodem. Zaś w konsoli na dole widać jak llm-router przyjmuje zapytania i kieruje do odpowiedniego hosta:

{{< video https://radlab.dev/wp-content/uploads/2025/10/pycharm-llm-router.webm >}}

Konfiguracja użyta do uruchomienia llm-routera:

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

I pełen skrypt z uruchomieniem dockera (to co uruchamiane jest w terminalu na filmie — czyli pełna konfiguracja i zmiana wszystkich domyślnych parametrów :)):

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

Jednym z miejsc, gdzie llm-router działa jest nasz playground. Każda funkcjonalność dotycząca modelu generatywnego oprogramowana jest jako dedykowany EP w llm-router.  Kody udostępniamy oczywiście na licencji Apache 2.0 — można brać i wykorzystywać komercyjnie i niekomercyjnie — smacznego!

Zachęcamy do korzystania i zgłaszania swoich sugestii i uwag.

> **Aktualizacja (Wydanie v1.1+):** Zapowiadane funkcjonalności (6 zaawansowanych strategii Load Balancingu, Redis Rate Limiting w przesuwnym oknie czasowym, metryki Prometheus oraz potok wtyczek maskowania PII i guardraili NASK/Sójka) zostały w pełni wdrożone! Zobacz [pełną specyfikację LLM Routera](/products/llm-router/).
