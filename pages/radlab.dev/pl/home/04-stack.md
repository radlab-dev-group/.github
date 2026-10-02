---
order: 4
layout: stack
anchor: stack
eyebrow: "Stos technologiczny"
title: "Fundament technologiczny naszych systemów"
intro: "Własne modele, routery i systemy AI budujemy w oparciu o sprawdzony, wydajny ekosystem open-source zoptymalizowany pod kątem suwerenności danych, minimalnych opóźnień i stabilności produkcyjnej."
pills:
  - {name: "PyTorch", role: "trening i dostrajanie modeli"}
  - {name: "Hugging Face", role: "ekosystem NLP i tokenizatory"}
  - {name: "vLLM", role: "silnik wnioskowania i PagedAttention"}
  - {name: "Ollama", role: "lokalne uruchamianie modeli"}
  - {name: "Milvus", role: "baza wektorowa i semantic search"}
  - {name: "FastAPI", role: "asynchroniczne mikroserwisy"}
  - {name: "Docker", role: "konteneryzacja środowisk"}
  - {name: "CUDA", role: "akceleracja sprzętowa GPU"}
cards:
  - title: "Modele i trenowanie"
    icon: "ml"
    text: "Rozwijamy rodzinę modeli pLLama, enkodery semantyczne i modele ekstrakcyjnego QA. Wykorzystujemy PyTorch, Transformers, FlashAttention oraz techniki efektywnego dostrajania (PEFT/LoRA) do pracy z polskimi korpusami."
    tags: ["PyTorch", "Transformers", "PEFT / LoRA", "FlashAttention", "Hugging Face"]
  - title: "Wnioskowanie i routing LLM"
    icon: "router"
    text: "Optymalizujemy czas odpowiedzi i przepustowość wnioskowania generatywnego. Integrujemy silniki vLLM, Ollama, llama.cpp i TensorRT-LLM, zapewniając sub-sekundowy streaming, dynamiczny fallback i ujednolicony interfejs API."
    tags: ["vLLM", "Ollama", "llama.cpp", "TensorRT-LLM", "Streaming API"]
  - title: "Bazy wektorowe i wyszukiwanie"
    icon: "data"
    text: "Systemy wyszukiwania semantycznego i zaawansowany RAG opieramy na wysokowydajnej bazie wektorowej Milvus. Przetwarzamy, klastrujemy i indeksujemy wielogigabajtowe zbiory danych z wykorzystaniem bibliotek FAISS i Polars."
    tags: ["Milvus", "FAISS", "Polars", "Semantic Search", "RAG"]
  - title: "Architektura i produkcja"
    icon: "code"
    text: "Przekładamy zaawansowane badania nad modelami na niezawodne środowiska on-premise i private cloud. Projektujemy asynchroniczne mikroserwisy w FastAPI i Pythonie z naciskiem na suwerenność danych, izolację kontenerową i akcelerację GPU."
    tags: ["Python", "FastAPI", "Docker", "CUDA", "On-Premise / Private Cloud"]
---
