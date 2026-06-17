# Wymagania sprzętowo-systemowe

Powrót do [agendy](00_agenda.md).

---

## Minimalne wymagania sprzętowe

Poniższa tabela przedstawia wymagania dla każdego z kroków tutorialu.

| Komponent  | Minimalne             | Zalecane                   | Uwagi                                                                                          |
|------------|-----------------------|----------------------------|------------------------------------------------------------------------------------------------|
| **CPU**    | 4 rdzenie             | 8+ rdzeni                  | Przy labelowaniu/augmentacji batchowej wielowątkowej więcej rdzeni = szybciej                  |
| **RAM**    | 16 GB                 | 32-128 GB+                 | 7B: 16GB, 70B: 64GB+, 120B: 96GB+ (zalecane przy braku GPU)                                    |
| **Dysk**   | 50 GB wolnego miejsca | 250 GB+                    | Bielik (~5GB), PLLuM (~40GB), gpt-oss (~65GB). Modele i datasety zajmują dużo miejsca          |
| **GPU**    | Nieobowiązkowe        | NVIDIA GPU z 24-80 GB VRAM | Bielik: 8GB, PLLuM: 48GB+ (Q4), gpt-oss: 80GB (lub multi-GPU)                                  |
| **System** | Linux / macOS 13+     | Linux (Ubuntu 22.04+)      | Linux jest platformą docelową; macOS z Apple Silicon działa dla Ollama/llama.cpp, ale VLLM nie |

---

## Wymagania systemowe

### System operacyjny

Tutorial jest zaprojektowany pod **Linux (Ubuntu 22.04+)**. Warianty:

| Element                 | Ubuntu 22.04+ | macOS (Apple Silicon) | Windows (WSL2)  |
|-------------------------|:-------------:|:---------------------:|:---------------:|
| VLLM                    |       ✅       |           ❌           |        ❌        |
| Ollama                  |       ✅       |           ✅           | ⚠️ (przez WSL2) |
| llama.cpp               |       ✅       |           ✅           |        ✅        |
| llm-router              |       ✅       |           ✅           |        ✅        |
| genai-classifier        |       ✅       |           ✅           |        ✅        |
| genai-data-augmentation |       ✅       |           ✅           |        ✅        |
| PyTorch / Transformers  |       ✅       |           ✅           |        ✅        |

### Python

Wymagany **Python 3.10+** (zalecane 3.12+).

```bash
python3 --version
# Powinno zwrócić: Python 3.10+
```

### Virtual environment

Zalecane użycie izolowanego `venv`:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Zależności Pythona

```bash
pip install -r requirements.txt
```

Główne pakiety: `torch`, `transformers`, `datasets`, `scikit-learn`, `matplotlib`, `wandb`, `flask`, `flask_sqlalchemy`.

---

Powrót do [agendy](00_agenda.md).
