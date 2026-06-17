# Wymagania sprzętowo-systemowe

Powrót do [agendy](00_agenda.md).

---

## Minimalne wymagania sprzętowe

Poniższa tabela przedstawia wymagania dla każdego z kroków tutorialu.

| Komponent  | Minimalne             | Zalecane                   | Uwagi                                                                                          |
|------------|-----------------------|----------------------------|------------------------------------------------------------------------------------------------|
| **CPU**    | 4 rdzenie             | 8+ rdzeni                  | Przy labelowaniu/augmentacji batchowej wielowątkowej więcej rdzeni = szybciej                  |
| **RAM**    | 16 GB                 | 32 GB+                     | Przy modelach 7B (Bielik) wystarczy 16GB, dla 70B (PLLuM) zalecane 64GB+ (jeśli bez GPU)       |
| **Dysk**   | 50 GB wolnego miejsca | 200 GB+                    | Bielik (5-8 GB), PLLuM (40-140 GB). Modele, venvy i datasety szybko zajmują miejsce            |
| **GPU**    | Nieobowiązkowe        | NVIDIA GPU z 24-80 GB VRAM | Bielik: 8GB VRAM (np. RTX 3060/4060). PLLuM: min. 48GB (np. A6000) dla Q4 lub 2x80GB dla FP16  |
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
