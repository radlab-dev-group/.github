---
order: 4
layout: stack
anchor: stack
eyebrow: "Stos technologiczny"
title: "Fundament technologiczny naszych systemów"
intro: "Łączymy modele językowe, wyszukiwanie semantyczne i narzędzia ochrony danych. Ten stos pozwala nam rozwijać własne rozwiązania — od lokalnej analizy wiadomości po zarządzanie ruchem między modelami."
pills:
  - {name: "PyTorch", role: "trening i dostrajanie modeli"}
  - {name: "Transformers", role: "modele językowe i klasyfikatory"}
  - {name: "Sentence-Transformers", role: "wektorowe reprezentacje tekstu"}
  - {name: "vLLM", role: "wnioskowanie modeli językowych"}
  - {name: "Ollama", role: "lokalne uruchamianie modeli"}
  - {name: "Milvus", role: "baza wektorowa i wyszukiwanie semantyczne"}
  - {name: "Redis", role: "koordynacja ruchu i limity zapytań"}
  - {name: "ONNX", role: "wnioskowanie modeli NER na CPU"}
cards:
  - title: "Modele i trenowanie"
    icon: "ml"
    text: "Rozwijamy modele dla języka polskiego: generatywne, enkodery semantyczne, modele ekstrakcyjnego QA i klasyfikatory NER. Korzystamy z PyTorch i ekosystemu Hugging Face, a w lokalnych eksperymentach sprawdzamy także możliwości małych modeli."
    tags: ["PyTorch", "Transformers", "Hugging Face", "NLP"]
  - title: "Wnioskowanie i routing LLM"
    icon: "router"
    text: "Łączymy lokalne silniki z API chmurowymi przez interfejs zgodny z OpenAI i endpoint Anthropic. Konfigurowalne wtyczki, routing i strategie balansowania pozwalają zarządzać ruchem, a Redis wspiera koordynację dostawców i limity zapytań."
    tags: ["vLLM", "Ollama", "llama.cpp", "LM Studio", "Redis"]
  - title: "Wyszukiwanie i analiza informacji"
    icon: "data"
    text: "Wyszukiwanie semantyczne opieramy na Milvusie i wektorowych reprezentacjach tekstu. Do wykrywania tematów używamy Sentence-Transformers, redukcji wymiarowości t-SNE lub UMAP i klastrowania HDBSCAN. Modele generatywne nadają tematom nazwy i tworzą podsumowania ze źródłami."
    tags: ["Milvus", "Sentence-Transformers", "HDBSCAN", "t-SNE / UMAP"]
  - title: "Anonimizacja i ochrona danych"
    icon: "shield"
    text: "Łączymy reguły i walidację sum kontrolnych z modelami NER dla języka polskiego. Maskowanie danych i guardraile można włączyć przed wywołaniem modelu. ONNX i kwantyzacja INT8 umożliwiają także uruchamianie modelu anonimizacji na CPU."
    tags: ["NER", "RoBERTa", "ONNX / INT8", "PII Masking", "Guardrails"]
---
