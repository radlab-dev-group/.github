# Klasyfikacja a generowanie

Ważnym elementem tutorialu jest rozróżnienie dwóch typów modeli: _klasyfikacyjnych_ i _generatywnych_.

Powrót do [agendy](00_agenda.md).

---

## Model klasyfikacyjny

Pprzypisuje dane wejściowe do jednej lub wielu z góry zdefiniowanych klas.

Przykład:

Wejście:
```text
„Nie mogę zalogować się do konta.”
```

Możliwe klasy:

- `problem_logowania`,
- `płatność`,
- `reklamacja`,
- `zwrot`,
- `inne`.

Wyjście modelu: `problem_logowania`

Model klasyfikacyjny najczęściej odpowiada na pytanie:
```text
Do której kategorii/klasy należy ten przykład?
```

W praktyce może zwracać również prawdopodobieństwa:

| Klasa              | Prawdopodobieństwo |
|--------------------|-------------------:|
| problem_logowania  |               0.87 |
| problem_techniczny |               0.09 |
| inne               |               0.04 |

To pozwala analizować nie tylko samą decyzję, ale również pewność modelu.

Modele klasyfikacyjne są używane między innymi do:

- wykrywania intencji,
- analizy sentymentu,
- detekcji spamu,
- klasyfikacji dokumentów,
- kategoryzacji opinii.

Ich zaletą jest to, że są zwykle szybsze, tańsze w uruchomieniu i łatwiejsze do wdrożenia w produkcji niż duże modele
generatywne. Dodatkowo pozwalają na weryfikację pewności, która opiera się na porównywaniu "liczb":
> np. można ustawić threshold, że klasa `spam` aktywuje się z zadanym progiem pewności, zaś klasa `ważne` z innym.

---

## Model generatywny

Tworzy nowe dane, w przypadku LLM-ów generuje tokeny, które przekładane są na reprezentację tekstową.

Przykład:

Prompt:
```text
Wygeneruj trzy alternatywne wersje zdania: „Chcę zwrócić produkt”.
```

Odpowiedź:
```text
„Jak mogę dokonać zwrotu zamówienia?”  
„Produkt mi nie odpowiada i chciałbym go odesłać.”  
„Proszę o informację, jak zwrócić zakupiony towar.”
```

Model generatywny odpowiada na pytanie:
```text
Jakie dane można wygenerować na podstawie kontekstu?
```

W naszym przypadku model generatywny nie jest modelem docelowym. On pełni rolę pomocniczą. Używamy go do przygotowania
lub rozszerzenia zbioru danych, na którym później możemy trenować albo dostrajać model klasyfikacyjny.

Czyli:

> LLM generatywny pomaga przygotować dane w formie tekstowej, a model klasyfikacyjny uczy się na tych danych podejmowania decyzji.

---

Powrót do [agendy](00_agenda.md).