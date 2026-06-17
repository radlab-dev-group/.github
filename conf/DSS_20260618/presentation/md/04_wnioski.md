# Podsumowanie i wnioski

Powrót do [agendy](00_agenda.md).

---

## Podsumowanie tutorialu

W ramach tutorialu zaprezentowaliśmy **kompletny pipeline augmentacji danych uczących** z wykorzystaniem lokalnych
LLMów, w tym:

- **Przygotowanie datasetu** — próbkowanie `clarin-pl/twitteremo` (5k train, 500 valid).
- **Labelowanie LLM** — automatyczne klasyfikowanie tekstów (`genai-classifier` z `llm-router-utils`) przez lokalny
  LLM (np. `gpt-oss:120b`).
- **Augmentacja danych** — generowanie nowych przykładów dla klasy `pozytywny` (`genai-data-augmentation` z
  `llm-router-utils`), ~1.7k dodatkowych samples.
- **Merge datasetów** — połączenie 5k manualnych + ~1.7k augmentowanych (~6.7k samples).
- **Trenowanie klasyfikatora** — fine-tuning `allegro/herbert-base-cased` na 3 wariantach (manual / manual+augment /
  manual+augment+HIL).
- **Web App** — wizualna ocena + anotacja (Flask + SQLite), interfejs do kontroli jakości.
- **Human in the Loop** — aktywny learning — użytkownik poprawia etykiety, dane wracają do treningu.

Kluczowe wnioski:

- Augmentacja LLM **zwiększa liczebność** klasy docelowej, ale jakość jest **kluczowa** (temperatura, prompt,
  validacja).
- HIL/AL **doprecyzowuje** dane — użytkownik wyciąga najbardziej niepewne przykłady.
- Łącząc dane manualne + augmentowane + HIL, model osiąga **lepsze wyniki** niż na jednym źródle.

---

## 1. Automatyczna ocena modelu po HIL/AL (podgląd w W&B)

Po każdej iteracji HIL/AL trening jest logowany do **Weights & Biases**:

- **Precision/Recall/Accuracy** — ogólna poprawność predykcji.
- **Macro F1** — średnia ważona F1 po klasach.
- **Confusion matrix** — które klasy są mylone.

> Na żywo — pokazujemy wyniki z W&B po anotacji w Web App.

---

## 2. Wnioski z wniosków

### Co zadziałało?

- ✅ **Automatyczne labelowanie** przyspiesza pracę 10×+ (5k przykładów w minuty vs dni).
- ✅ **Augmentacja LLM** zwiększa liczebność klasy `pozytywny` — lepszy recall dla tej klasy.
- ✅ **Web App** daje wizualny wgląd — użytkownicy szybko wskazują błędy.
- ✅ **HIL/AL** koncentruje się na **najtrudniejszych** przykładach — maksymalna wartość na godzinę pracy.

### Na co uważać?

- ⚠️ Augmentacja bez HIL może **pogorszyć wynik**, jeśli LLM generuje błędne/nieistotne przykłady.
- ⚠️ Temperatura > 0.0 zwiększa różnorodność, ale **wzrasta prawdopodobieństwo "halucynacji"**.
- ⚠️ LLM może mieć **bias** — jeśli model trenowany jest na danych niebalansowanych, może powielać błędy.

### Wnioski po sesji anotacji LIVE

> W trakcie tutorialu - zależy w jaki sposób wyuczy się model

---

Powrót do [agendy](00_agenda.md).
