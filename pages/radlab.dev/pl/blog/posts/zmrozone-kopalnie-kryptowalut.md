---
title: "Zmrożone kopalnie kryptowalut?"
date: 2026-01-01
slug: zmrozone-kopalnie-kryptowalut
description: "Dzisiaj nieco z innej „bajki”. Nie technicznie od strony wytwórczej, a być może propozycja częściowego rozwiązania problemu z mediów do czego można jeszcze…"
tags: ["crypto-minig", "genai", "llm", "llm-router", "local", "open-source", "saas"]
categories: ["Bezpieczeństwo", "Crypto-mining", "GenAI", "LLM", "LLM Router", "Load balancing", "narzędzia", "On-prem", "open-source", "SaaS"]
image: media/zmrozone-kopalnie-kryptowalut/_featured.avif
lang: pl
wp_id: 4523
---

**Dzisiaj** nieco z innej „bajki”. Nie technicznie od strony wytwórczej, a być może **propozycja** częściowego **rozwiązania** **problemu** z mediów do czego można jeszcze wykorzystać „zamrożone” kopalnie kryptowalut 😉 np. [LINK](https://www.benchmark.pl/aktualnosci/odchodza-od-kryptowalut-ai.html). Biorąc pod uwagę zapotrzebowanie na moce obliczeniowe potrzebne do uczenia modeli nie każda karta będzie odpowiednia do tego celu (potrzebne są karty z bardzo dużą ilością vRAM). W tym wpisie pokażemy jak zmienić nośnik USB w **gotowe** **środowisko** **obliczeniowe**, do którego podepniemy **[LLM Router](https://llm-router.cloud/)** jako warstwę **komunikacyjną** z **modelami** generatywnymi.

![](@media/zmrozone-kopalnie-kryptowalut/01-router-crypto-miner-btc.avif)

Jeżeli **posiadasz** już gotowe **środowisko** do **kopania** **kryptowalut**, śmiało możesz **pominąć** krok **Instalacji** HiveOS. **Jeśli** **nie**, to przejście przez ten **krok** **pomaga** w **przygotowaniu** **systemu**. W opisie wykorzystany został **USB** jako **nośnik** systemu, ponieważ **HiveOS** **domyślnie** instalowany jest na **USB**.

## Intro

Jak zatem **llm-router** może **pomóc** w rozwiązaniu tego problemu? Propozycja jest w sumie dość oczywista i prosta, **wykorzystanie** **zasobów** **kopalni** **kryptowalut**, jako **providera** do świadczenia usług **inferencji** **modeli** generatywnych. Czyli, **jeżeli** **posiadasz** już gotową **infrastrukturę**, ten wpis pokaże Ci jak **wykorzystać** ją do **uruchamiania** **modeli** generatywnych. Dzięki temu będziesz miał **działającą** **lokalnie** **usługę** uruchamiania **modeli** takich jak *gpt-oss* czy *gemma*. A co z tym fantem można zrobić? Np. **świadczyć** **płatną** **usługę** do **obliczeń** (inferencji) właśnie na tych modelach.

## Instalacja HiveOS

Pierwszym krokiem jest zainstalowanie gotowego systemu ze skonfigurowanymi sterowanikami do kart graficznych. Przykładowo może to być [HiveOS](https://hiveon.com/) (samo Ubuntu-desktop też nie jest najgorszym rozwiązaniem, jeśli nie chcemy przejmować się instalacją bibliotek do obsługi sterowników GPU). Proces instalacji przedstawiony jest dokładnie na oficjalnej stronie [https://hiveon.com/install](https://hiveon.com/install) – aktualnie dostępna wersja oparta jest o Ubuntu 22.04.

![](@media/zmrozone-kopalnie-kryptowalut/02-image.avif)

Wybieramy oczywiście GPU (lub beta z nowymi sterownikami dla odważnych ;-)) i instalujemy zgodnie z *[How to Write Image](https://hiveon.com/install/#howto-image)*. W przykładzie wykorzystaliśmy instalację na USB za pomocą wbudowanego w Ubuntu narzędzia do nagrywania obrazów (można również skorzystać z  [balenaEtcher](https://etcher.balena.io/)).

![](@media/zmrozone-kopalnie-kryptowalut/03-image-4.avif)

Po instalacji domyślny użytkownik to `user` a hasło to `1`. Oczywiście dobrym zwyczajem jest zmiana domyślnego hasła na bardziej skomplikowane (po zalogowaniu na maszynę z GPU`passwd`).

## Konfiguracja OS

Pomijamy tutaj proces konfiguracji serwera z kartami jako RIG do obliczeń w HiveOS (wydobywania kryptowalut i monitorowania procesu w interfejsie HiveOS’a). Wykorzystujemy fakt już skonfigurowanego systemu, do którego doinstalujemy kilka podstawowych bibliotek systemowych, które wymagane będą do uruchomienia lokalnie swojej isntancji LLM Routera w konfiguracji z modelem dostępnym przez *Ollamę*. Lokalny provider jest oczywiście dowolny: Ollama, vLLM, llama.cpp – bez znaczenia, LLM Router jest interfejsem, który komunikuje się z dowolnym protokołem lokalnego providera modeli. Po zalogowaniu się na maszynę z postawionym HiveOS: `ssh user@IP.LOKALNE.MASZYNY` dostaniemy informację odnośnie załadowanych driverów i dostępnych kart graficznych:

![](@media/zmrozone-kopalnie-kryptowalut/04-image-5.avif)

W naszym przypadku dostępne są trzy karty RTX 3090, każda po 24GB VRAM. Dokładne informacje odnośnie limitów, temperatury itp. można podejrzeć komendą `nvidia-info` (dla kart Nvidii):

![](@media/zmrozone-kopalnie-kryptowalut/05-image-6.avif)

Teraz wystarczy doinstalować podstawowe pakiety `pip` (do instalacji zależności) oraz `git` (do klonowania repozytorium):

```bash
# Instalacja w systemie (jeżeli nie ma) git + pip
apt install git python3-pip -y
```

Właściwie te dwa dodatkowe pakiety wystarczą aby system operacyjny był już skonfigurowany do uruchomienia LLM Routera.

## Instalacja LLM Routera

W przykładzie pokazujemy w jaki sposób uruchomić natywnie (nie z obrazu dockerowego) najnowszą wersję LLM Routera z głównej gałęzi `main`.

```bash
# Klonowanie rpozytorium llm-router
git clone https://github.com/radlab-dev-group/llm-router

# Instalacja zależności oraz API
cd llm-router/
pip install -r requirements.txt
pip install .[api]
```

I tyle, w skrócie: pobranie, instalacja, uruchomienie w 3 komendach :). Teraz wydając komendę: `./run-rest-api-gunicorn.sh` wystawiamy gotowe API za pomocą Gunicorna, jeszcze bez podpiętych modeli, ale już z działająca usługa sieciową (REST Api):

### Zobacz log z uruchomienia \[KLIK\]+

```json
root@HiveOS:/home/user/llm-router# ./run-rest-api-gunicorn.sh
2026-01-01 17:59:14,058 INFO main: Starting LLM‑Router API with gunicorn
2026-01-01 17:59:14,065 DEBUG llm_router_api.core.lb.provider_strategy_facade: [provider-monitor] keys to check: []
2026-01-01 17:59:14,072 INFO llm_router_api.core.lb.provider_strategy_facade: [Load balancing] Strategy FirstAvailableStrategy
2026-01-01 17:59:14,072 DEBUG llm_router_api.core.monitor.services_monitor: [services-monitor] thread started
2026-01-01 17:59:14,077 DEBUG llm_router_api.register.auto_loader: Instantiating OpenAICompletionHandlerWOApi
2026-01-01 17:59:14,078 DEBUG llm_router_api.register.auto_loader: Instantiating AnswerBasedOnTheContext
2026-01-01 17:59:14,078 DEBUG llm_router_api.register.auto_loader: Instantiating OpenAICompletionHandler
2026-01-01 17:59:14,078 DEBUG llm_router_api.register.auto_loader: Instantiating OpenAIModelsV1Handler
2026-01-01 17:59:14,078 DEBUG llm_router_api.register.auto_loader: Instantiating ApiVersion
2026-01-01 17:59:14,078 INFO llm_router_api.endpoints.endpoint_i: -> Running LLM-Router version: 0.4.4
2026-01-01 17:59:14,078 DEBUG llm_router_api.register.auto_loader: Instantiating OpenAIResponsesV1Handler
2026-01-01 17:59:14,078 DEBUG llm_router_api.register.auto_loader: Instantiating Ping
2026-01-01 17:59:14,078 DEBUG llm_router_api.register.auto_loader: Instantiating OpenAIResponsesHandler
2026-01-01 17:59:14,078 DEBUG llm_router_api.register.auto_loader: Instantiating ConversationWithModel
2026-01-01 17:59:14,078 DEBUG llm_router_api.register.auto_loader: Instantiating FullArticleFromTexts
2026-01-01 17:59:14,078 DEBUG llm_router_api.register.auto_loader: Instantiating ExtendedConversationWithModel
2026-01-01 17:59:14,078 DEBUG llm_router_api.register.auto_loader: Instantiating GenerateNewsFromTextHandler
2026-01-01 17:59:14,078 DEBUG llm_router_api.register.auto_loader: Instantiating TranslateTexts
2026-01-01 17:59:14,078 DEBUG llm_router_api.register.auto_loader: Instantiating SimplifyTexts
2026-01-01 17:59:14,079 DEBUG llm_router_api.register.auto_loader: Instantiating OllamaTagsHandler
2026-01-01 17:59:14,079 DEBUG llm_router_api.register.auto_loader: Instantiating GenerateQuestionsFromTexts
2026-01-01 17:59:14,079 DEBUG llm_router_api.register.auto_loader: Instantiating LLMStudioChatV0Handler
2026-01-01 17:59:14,079 DEBUG llm_router_api.register.auto_loader: Instantiating OllamaHomeHandler
2026-01-01 17:59:14,079 DEBUG llm_router_api.register.auto_loader: Instantiating FastTextMasking
2026-01-01 17:59:14,079 DEBUG llm_router_api.register.auto_loader: Instantiating VllmChatCompletion
2026-01-01 17:59:14,079 DEBUG llm_router_api.register.auto_loader: Instantiating LmStudioModelsHandler
2026-01-01 17:59:14,079 DEBUG llm_router_api.register.auto_loader: Instantiating OpenAIModelsHandler
2026-01-01 17:59:14,079 DEBUG llm_router_api.register.auto_loader: Instantiating OllamaChatHandler
2026-01-01 17:59:14,079 INFO llm_router_api.register.register: Registered endpoint POST /chat/completions (OpenAICompletionHandlerWOApi)
2026-01-01 17:59:14,079 INFO llm_router_api.register.register: Registered endpoint POST /api/generative_answer (AnswerBasedOnTheContext)
2026-01-01 17:59:14,080 INFO llm_router_api.register.register: Registered endpoint POST /api/chat/completions (OpenAICompletionHandler)
2026-01-01 17:59:14,080 INFO llm_router_api.register.register: Registered endpoint GET /v1/models (OpenAIModelsV1Handler)
2026-01-01 17:59:14,080 INFO llm_router_api.register.register: Registered endpoint GET /api/version (ApiVersion)
2026-01-01 17:59:14,080 INFO llm_router_api.register.register: Registered endpoint POST /v1/responses (OpenAIResponsesV1Handler)
2026-01-01 17:59:14,080 INFO llm_router_api.register.register: Registered endpoint GET /api/ping (Ping)
2026-01-01 17:59:14,081 INFO llm_router_api.register.register: Registered endpoint POST /responses (OpenAIResponsesHandler)
2026-01-01 17:59:14,081 INFO llm_router_api.register.register: Registered endpoint POST /api/conversation_with_model (ConversationWithModel)
2026-01-01 17:59:14,081 INFO llm_router_api.register.register: Registered endpoint POST /api/create_full_article_from_texts (FullArticleFromTexts)
2026-01-01 17:59:14,081 INFO llm_router_api.register.register: Registered endpoint POST /api/extended_conversation_with_model (ExtendedConversationWithModel)
2026-01-01 17:59:14,081 INFO llm_router_api.register.register: Registered endpoint POST /api/generate_article_from_text (GenerateNewsFromTextHandler)
2026-01-01 17:59:14,081 INFO llm_router_api.register.register: Registered endpoint POST /api/translate (TranslateTexts)
2026-01-01 17:59:14,082 INFO llm_router_api.register.register: Registered endpoint POST /api/simplify_text (SimplifyTexts)
2026-01-01 17:59:14,082 INFO llm_router_api.register.register: Registered endpoint GET /api/tags (OllamaTagsHandler)
2026-01-01 17:59:14,082 INFO llm_router_api.register.register: Registered endpoint POST /api/generate_questions (GenerateQuestionsFromTexts)
2026-01-01 17:59:14,082 INFO llm_router_api.register.register: Registered endpoint POST /api/v0/chat/completions (LLMStudioChatV0Handler)
2026-01-01 17:59:14,082 INFO llm_router_api.register.register: Registered endpoint GET / (OllamaHomeHandler)
2026-01-01 17:59:14,082 INFO llm_router_api.register.register: Registered endpoint POST /api/fast_text_mask (FastTextMasking)
2026-01-01 17:59:14,083 INFO llm_router_api.register.register: Registered endpoint POST /v1/chat/completions (VllmChatCompletion)
2026-01-01 17:59:14,083 INFO llm_router_api.register.register: Registered endpoint GET /api/v0/models (LmStudioModelsHandler)
2026-01-01 17:59:14,083 INFO llm_router_api.register.register: Registered endpoint GET /models (OpenAIModelsHandler)
2026-01-01 17:59:14,083 INFO llm_router_api.register.register: Registered endpoint POST /api/chat (OllamaChatHandler)
2026-01-01 17:59:14,083 INFO llm_router_api.core.metrics: [Prometheus] preparing metrics request hooks
2026-01-01 17:59:14,083 INFO llm_router_api.core.metrics: [Prometheus] registering metrics request hooks
[2026-01-01 17:59:14 +0000] [147288] [INFO] Starting gunicorn 23.0.0
[2026-01-01 17:59:14 +0000] [147288] [INFO] Listening at: http://0.0.0.0:8080 (147288)
[2026-01-01 17:59:14 +0000] [147288] [INFO] Using worker: gthread
[2026-01-01 17:59:14 +0000] [147296] [INFO] Booting worker with pid: 147296
[2026-01-01 17:59:14 +0000] [147297] [INFO] Booting worker with pid: 147297
[2026-01-01 17:59:14 +0000] [147298] [INFO] Booting worker with pid: 147298
[2026-01-01 17:59:14 +0000] [147299] [INFO] Booting worker with pid: 147299
2026-01-01 17:59:19,066 DEBUG llm_router_api.core.lb.provider_strategy_facade: [provider-monitor] keys to check: []
```

---

Log zawiera informacje z trybu DEBUG, więc jest ich całkiem sporo. Jest to domyślny poziom logowania, który dowolnie może być zmieniony.

## Przykładowa konfiguracja: Ollama + gpt-oss:120b

Teraz zajmiemy się instalacją Ollamy z udostępnieniem modelu o wielkości 120b parametrów (gpt-oss:120b). Model jest na dyle duży, że wymaga 3 kart RTX z 24GB VRAM każda. Ollama potrafi bardzo dobrze uruchomić ten model na 3 kartach, zachowując przy tym niemalże pełną obsługę długości kontekstu. Zamykamy uruchomioną instancję LLM Routera (CTRL+C) i instalujemy Ollamę – instacja jest banalna, wystarczy w konsoli wywołać oficjalny skrypt instalacyjny:

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Po chwili (zależy jakie łącze internetowe) Ollama jest gotowa i należy załadować na nią model lokalny. Dokładny opis jak zrobić to lokalnie znajduje się na stronie karty modelu: [https://ollama.com/library/gpt-oss](https://ollama.com/library/gpt-oss). Wystarczy:

```text
ollama run gpt-oss:120b
```

Po pobraniu, model od razu dostępny jest w lokalnej instancji Ollamy.

{{< callout >}}

**UWAGA**!

Model gpt-oss:120b dostępny za pomocą Ollama to skwantyzowana wersja gpt-oss-120b od OpenAI. Pomimo dużej kwantyzacji model nadal jest bardzo duży, zajmuje około 65GB na dysku (i tyle samo w pamięci kart graficznych), dlatego pendrive musi być odpowiednio duży aby lokalnie zmieścić ten model (ewentualnie można podmontować dysk z dostępnym modelem).

{{< /callout >}}

**OPCJA:** Jeżeli model jest już pobrany i dostępny w ramach sieci, można podłączyć model z dysku sieciowego zamiast pobierać na pendrive. Przykład jak na 3 kartach uruchomić model dostępny w ramach sieci (np. po nfs) z katalogu `/mnt/data2/llms/models/ollama/.ollama/models/`:

```text
CUDA_VISIBLE_DEVICES=0,1,2 \
  OLLAMA_NOPRUNE=true \
  OLLAMA_CONTEXT_LENGTH=128000 \
  OLLAMA_MODELS=/mnt/data2/llms/models/ollama/.ollama/models/ \
  OLLAMA_HOST=0.0.0.0 \
  ollama serve
```

Aby sprawdzić jakie modele dostępne są w Ollamie wystarczy polecenie `ollama list`. Przykładowo u nas (z podmontowanego dysku sieciowego):

```text
root@HiveOS:/home/user/llm-router# ollama list
NAME                           ID              SIZE      MODIFIED
dolphin-mistral:latest         5dc8c5a2be65    4.1 GB    5 days ago
dolphin3:8b                    d5ab9ae8e1f2    4.9 GB    6 days ago
devstral-2:latest              524a6607f0f5    74 GB     6 days ago
devstral-2:123b                524a6607f0f5    74 GB     6 days ago
deepseek-r1:70b                d37b54d01a76    42 GB     4 weeks ago
gemini-3-pro-preview:latest    91a1db042ba1    -         4 weeks ago
gpt-oss:120b-ctx32k-rope       c265a9f5b5de    65 GB     7 weeks ago
gpt-oss:120b-ctx250k           964592b444fd    65 GB     7 weeks ago
glm-4.6:cloud                  05277b76269f    -         8 weeks ago
qwen3-coder:30b                06c1097efce0    18 GB     2 months ago
qwen3:235b                     72840bddff91    142 GB    3 months ago
gpt-oss:120b                   f7f8e2f8f4e0    65 GB     4 months ago
gpt-oss:20b                    aa4295ac10c3    13 GB     4 months ago
```

## Konfiguracja LLM Routera do obsługi gpt-oss:120b

Ok, to posiadamy już system, mamy pobrany router oraz załadowany model do Ollamy. Teraz pora podpiąć model do routera. Wcześniejsze polecenia uruchamiają model na tej samej maszynie, na której uruchomiony jest llm-router. Aby uprościć demonstrację udostępniliśmy również plik konfiguracyjny, który wystarczy podpiąć do uruchamianego routera (nadpisać domyślny plik konfiguracyjny):

- Można albo zmodyfikować w skrypcie uruchomieniowym run-rest-api-gunicorn.sh domyślną ścieżkę do konfigu (zmienna LLM\_ROUTER\_MODELS\_CONFIG )
- lub prościej: do procesu routera przekazać przy uruchamianiu ścieżkę do gotowej konfiguracji. Czyli wydać po prostu komednę:

```text
LLM_ROUTER_MODELS_CONFIG=resources/configs/specific/models-config-local-ollama.json ./run-rest-api-gunicorn.sh
```

I właściwie, to tyle 🙂 Można już odpytywać router podając nazwę modelu. Przykład w `curlu` i formatowaniem do jsona za pomocą `jq`:

```bash
curl -X POST http://localhost:8080/v1/chat/completions -H "Content-Type: application/json" -d '{"model": "gpt-oss:120b", "messages": [{"role": "user", "content": "Cześć"}]}' | jq
```

co powinno dać wynik zbliżony do:

![](@media/zmrozone-kopalnie-kryptowalut/06-image-7.avif)

## Outro

Te kilka opisanych kroków wystarczy na uruchomienie na sprzęcie oraz systemie typowo do wydobywania kryptowalut LLM Routera wykorzystującego te zasoby. Oczywiście to jest tylko przykład, na [repozytorium](https://github.com/radlab-dev-group/llm-router/tree/main/resources/configs) podaliśmy więcej przykładów modeli i łączenia do różnych lokalnych providerów.

**Górnicy, to druga szansa! 🙂**

Dobrego w nowym roku! Dbajcie o dane i nie wysyłajcie do chmury danych wrażliwych!
