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
    href: "products/playground"
    text: "Rozwijamy autorskie modele dla języka polskiego: generatywne pLLama, enkodery semantyczne, ekstrakcyjne QA oraz klasyfikatory NER. Korzystamy z PyTorch i ekosystemu Hugging Face, optymalizując je do wydajnego działania także na lokalnym sprzęcie (RDL Playground AI)."
    tags: ["PyTorch", "Transformers", "Hugging Face", "pLLama / QA"]
  - title: "Wnioskowanie i routing LLM"
    icon: "router"
    href: "products/llm-router"
    text: "Architektura bramy LLM Router łączy silniki lokalne (vLLM, Ollama) z chmurą przez API OpenAI/Anthropic. Obsługuje konfigurowalne potoki wtyczek, zaawansowane strategie równoważenia obciążenia i koordynację w Redis, gwarantując pełną kontrolę on-premise."
    tags: ["LLM Router", "vLLM", "Ollama", "Redis", "Load Balancing"]
  - title: "Wyszukiwanie i analiza informacji"
    icon: "data"
    href: "products/radar"
    text: "Silnik analityczny Radaru Informacji: wyszukiwanie semantyczne w Milvusie, ekstrakcja gęstych wektorów, nieliniowa redukcja wymiarowości (t-SNE/UMAP) oraz dynamiczne klastrowanie HDBSCAN do bezkategoryzacyjnego wykrywania trendów w strumieniach wiadomości."
    tags: ["Radar Informacji", "Milvus", "HDBSCAN", "Sentence-Transformers"]
  - title: "Anonimizacja i ochrona danych"
    icon: "shield"
    href: "products/pii-masker"
    text: "Fundament systemu PII Masker: dwuwarstwowa ochrona danych osobowych (deterministyczny FastMasker z sumami kontrolnymi + model RoBERTa NER). Kwantyzacja ONNX INT8 umożliwia maskowanie na CPU, wspierając minimalizację danych w projektach objętych RODO/GDPR i AI Act."
    tags: ["PII Masker", "FastMasker", "RoBERTa NER", "ONNX INT8", "RODO / GDPR"]
---
