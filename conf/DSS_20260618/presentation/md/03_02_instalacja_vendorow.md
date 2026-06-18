# Instalacja lokalnych silników (vendorów)

Powrót do [agendy](00_agenda.md).

---

## VLLM

vLLM to wysokowydajny silnik (high-throughput engine) do serwowania modeli LLM, zaprojektowany z myślą o maksymalnej
wydajności i skalowalności.

### Wymagania

- **Karta graficzna NVIDIA** z pamięcią VRAM ≥ 24 GB (zalecane ≥ 40 GB dla dużych modeli)
- Linux (nie obsługuje macOS/Windows natywnie)
- CUDA 12.x

### Instalacja

```bash
# Instalacja vLLM (wymaga GPU NVIDIA)
pip install vllm

# Weryfikacja
python3 -c "import vllm; print(vllm.__version__)"
```

### Uruchomienie serwera (Llama-PLLuM-70B)

```bash
# Uruchomienie modelu PLLuM 70B na dwóch układach GPU (Tensor Parallelism)
vllm serve CYFRAGOVPL/Llama-PLLuM-70B-chat-2512 \
  --tensor-parallel-size 2 \
  --max-model-len 8192 \
  --port 8080
```

Po uruchomieniu serwer jest dostępny pod adresem `http://localhost:8080` (lub pod adresem IP serwera w sieci lokalnej).

### Uwagi

- vLLM oferuje wsparcie dla **tensor parallelism**, co pozwala na efektywne rozłożenie modelu na wiele kart GPU.
- Obsługuje modele w formacie **Hugging Face (Safetensors)** oraz nowsze wersje formatu **GGUF**.

---

## Ollama

Ollama to proste w obsłudze narzędzie do lokalnego uruchamiania modeli LLM, wymagające minimalnej konfiguracji.
Obsługuje szeroką gamę akceleratorów GPU (NVIDIA, AMD, Apple Silicon) oraz procesory CPU.

### Instalacja (Linux)

```bash
# Oficjalny skrypt instalacyjny
curl -fsSL https://ollama.com/install.sh | sh

# Uruchomienie usługi w tle
ollama serve &
```

### Pobranie i uruchomienie modeli (Bielik, PLLuM oraz gpt-oss)

Szczegółowy przewodnik od A - Z do instalacji Bielika (`speakleash/Bielik-11B-v2.3-Instruct`) : 
[KLIK](https://github.com/radlab-dev-group/llm-router/blob/main/examples/quickstart/speakleash-bielik-11b-v2_3-Instruct/README.md)

Bielik oraz gpt-oss są dostępne bezpośrednio w oficjalnej bibliotece Ollama. PLLuM można uruchomić, korzystając z
repozytoriów na
Hugging Face:

```bash
# Pobranie i uruchomienie interaktywne (Bielik)
ollama run SpeakLeash/bielik-minitron-7B-v3.0-instruct

# Model PLLuM (poprzez bibliotekę Hugging Face - GGUF)
ollama run hf.co/bartowski/Llama-PLLuM-70B-chat-2512-GGUF:Q4_K_M

# Model gpt-oss (duży model 120B od OpenAI, wymaga ok. 65 GB pamięci lub np 3x24GB)
ollama run gpt-oss:120b
```

### Instalacja (macOS)

Aplikację można pobrać bezpośrednio ze strony [ollama.com](https://ollama.com) lub zainstalować za pomocą menedżera
pakietów Homebrew:

```bash
brew install ollama
# Uruchomienie usługi
ollama serve
# Pobranie i uruchomienie modelu Bielik
ollama run SpeakLeash/bielik-minitron-7B-v3.0-instruct
```

### Interfejs API

Ollama automatycznie udostępnia API pod adresem:

```
http://localhost:11434
```

Może być ono wykorzystane przez narzędzia takie jak `llm-router` do komunikacji z lokalnymi modelami.

### Uwagi

- Natywnie obsługuje modele w formacie **GGUF**.
- Najbardziej przyjazne dla użytkownika rozwiązanie spośród prezentowanych silników.

---

## llama.cpp

llama.cpp to lekki i wydajny silnik napisany w C/C++, przeznaczony do inferencji modeli LLM na szerokiej gamie sprzętu (
CPU i GPU).

### Instalacja

```bash
# Klonowanie repozytorium kodu źródłowego
git clone https://github.com/ggerganov/llama.cpp.git
cd llama.cpp

# Budowanie projektu (z obsługą GPU NVIDIA - CUDA)
cmake -B build -DGGML_CUDA=ON
cmake --build build --config Release -j$(nproc)

# Budowanie bez wsparcia GPU (tylko procesor CPU)
cmake -B build
cmake --build build --config Release -j$(nproc)
```

### Pobranie modelu

Modele w formacie GGUF (np. z Hugging Face):

```bash
# Przykładowo z huggingface-cli:
pip install huggingface_hub
huggingface-cli download <model-repo> --include "*.gguf*" --local-dir models/
```

### Uruchomienie serwera

```bash
./build/bin/llama-server \
  --model models/model.gguf \
  --port 8080 \
  --host 0.0.0.0
```

### Uwagi

- llama.cpp opiera się na formacie **GGUF**. Modele w innym formacie wymagają uprzedniej konwersji.
- Oferuje największą kontrolę nad parametrami pracy modelu, kosztem bardziej złożonej konfiguracji.

---

## Porównanie narzędzi

| Cecha                    |      VLLM       |        Ollama         |        llama.cpp        |
|--------------------------|:---------------:|:---------------------:|:-----------------------:|
| **GPU support**          | ✅ NVIDIA (CUDA) | ✅ ROCm / Metal / CUDA | ✅ CUDA / Metal / Vulkan |
| **CPU-only**             |        ❌        |           ✅           |            ✅            |
| **macOS**                |        ❌        |           ✅           |            ✅            |
| **Windows**              |        ❌        |       ❌ (WSL2)        |            ✅            |
| **Dostępność API**       |        ✅        |           ✅           |            ✅            |
| **Łatwość konfiguracji** |     Średnia     |         Łatwa         |         Trudna          |
| **Wydajność (GPU)**      |  Bardzo wysoka  |        Wysoka         |         Wysoka          |
| **Wydajność (CPU)**      |      Brak       |         Dobra         |      Bardzo dobra       |
| **Dla modeli 120B+**     |  ✅ (multi-GPU)  | ⚠️ (wymaga GGUF/RAM)  |  ⚠️ (wymaga GGUF/RAM)   |

---

Powrót do [agendy](00_agenda.md).
