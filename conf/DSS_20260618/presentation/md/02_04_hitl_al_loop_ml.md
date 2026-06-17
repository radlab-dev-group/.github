# Pętla HITL z wykorzystaniem AL na danych augmentowanych

Powrót do [agendy](00_agenda.md).

---

**Augmentacja danych** odpowiada na pytanie:

> Jak zwiększyć i urozmaicić zbiór danych?

**Active Learning** odpowiada na pytanie:

> Które dane są najbardziej warte uwagi?

**Human in the Loop** odpowiada na pytanie:

> Jak utrzymać jakość i kontrolę nad procesem?

W praktyce można zbudować pętlę:

```text
Zbiór danych
    ↓
Trening klasyfikatora
    ↓
Analiza błędów i niepewności
    ↓
Wybór klas / przykładów do augmentacji
    ↓
Generowanie danych przez lokalny LLM
    ↓
Walidacja automatyczna i/lub ręczna
    ↓
Aktualizacja zbioru
    ↓
Ponowny trening klasyfikatora
```

Taka pętla jest znacznie bezpieczniejsza i w pełni kontrolowana, niż proste podejście:
```text
Weź dane → wygeneruj 10 razy więcej → trenuj model
```
Samo zwiększenie liczby przykładów nie gwarantuje poprawy jakości.

> TODO PRZYKŁAD PO LABELOWANIU - rozkład klas

Czasem może nawet pogorszyć wynik, jeśli wygenerowane przykłady są błędne, zbyt podobne albo nierealistyczne.

---

Powrót do [agendy](00_agenda.md).
