# Active Learning (AL) i Human In The Loop (HITL)

Powrót do [agendy](00_agenda.md).

## AL - ogólne podejście

To proces, w którym np. model aktywnie wskazuje, które przykłady są najbardziej wartościowe do oznaczenia,
sprawdzenia lub rozszerzenia. W typowym procesie uczenia nadzorowanego mamy zbiór danych, etykiety i trenujemy model.
W AL dodajemy pętlę zwrotną -- zamiast losowo wybierać dane do oznaczania, wybieramy te, które są najbardziej
informacyjne.

Najczęściej są to przykłady, dla których model:

- ma niską pewność predykcji,
- myli się między dwiema podobnymi klasami,
- wskazuje wysokie prawdopodobieństwo dla kilku klas naraz,
- jest niezgodny z innym modelem lub regułą,
- reprezentuje rzadką albo problematyczną część danych.

Przykład:

| Tekst                                               | Przykłądowe prawdopodobieństwa modelu                               |
|-----------------------------------------------------|---------------------------------------------------------------------|
| „Nie dostałem produktu i chcę pieniądze z powrotem” | zwrot: 0.42, reklamacja: 0.39, status_dostawy: 0.15, nieznany: 0.04 |

Dla modelu to trudny przykład. Nie jest pewien, czy chodzi o zwrot, reklamację, czy problem z dostawą.
Tak przykład jest szczególnie cenny, bo jego poprawne oznaczenie (i podobnych przypadków)
pomoże w trakcie treningu rozróżniania klas granicznych.

---

## AL w kontekście augmentacji

AL można powiedzieć, że odpowiada na pytanie:

```text
Które dane warto augmentować?
```

Nie zawsze ma sens augmentowanie całego zbioru po równo. Jeśli mamy 5000 przykładów klasy `status_zamówienia`
i tylko 50 przykładów klasy `fraud`, to prawdopodobnie większą wartość przyniesie augmentacja klasy rzadkiej.

Warto jednak pamiętać, liczebność klasy to nie wszystko -- wartp uwzględnić również:

- klasy, dla których model ma najgorsze wyniki,
- przykłady z pogranicza kilku klas,
- przypadki, które człowiek uważa za ważne biznesowo,
- przykłady, przy których model ma niską pewność,
- dane reprezentujące nietypowe warianty językowe,
- przykłady z błędami, skrótami, slangiem lub chaotycznym stylem.

Przykładowy proces:

```plain text
1. Trenujemy pierwszy prosty klasyfikator.
2. Sprawdzamy, na których przykładach się myli.
3. Identyfikujemy klasy lub typy przypadków problematycznych.
4. Dla tych obszarów generujemy dodatkowe przykłady przy pomocy LLM-a.
5. Człowiek lub reguły walidacyjne sprawdzają jakość augmentacji.
6. Trenujemy model ponownie.
7. Porównujemy wyniki.
```

To pozwala traktować augmentację nie jako jednorazowe "dogenerowanie danych", ale jako kontrolowany proces poprawiania
zbioru, a tym samym jakości modelu klasyfikacyjnego.

---

## HITL (Human In The Loop)

> Człowiek jest świadomą częścią procesu uczenia, walidacji czy też podejmowania decyzji.

### Human w HITL: Definiuje reguły i założenia

Człowiek określa:

- jakie klasy istnieją,
- co dokładnie oznacza każda klasa,
- jakie przykłady są poprawne,
- czego model generatywny nie powinien robić,
- jakie przypadki są niedopuszczalne,
- gdzie przebiega granica między klasami.

---

### Human w HITL: Sprawdza jakość wygenerowanych przykładów

Człowiek może oceniać, czy wygenerowany przykład:

- pasuje do etykiety,
- jest realistyczny,
- nie zawiera sprzeczności,
- nie powiela zbyt mocno oryginału,
- nie zawiera danych wrażliwych,
- nie wprowadza błędnego rozkładu danych.

---

### Human w HITL: Rozstrzyga przypadki niejednoznaczne

Modele często mają problem z przykładami, które dla człowieka również są niejednoznaczne.

Np.:

```text
„Nie dostałem paczki, więc chcę zwrot pieniędzy.”
```

Czy to jest:

- problem z dostawą,
- reklamacja,
- zwrot,
- sprawa finansowa?

Odpowiedź zależy od definicji klas, co w HITL pozwala utrzymać spójność tych decyzji ("koordynator").

---

### Human w HITL: Kontroluje proces uczenia

Człowiek analizuje metryki, błędy i jakość danych. Nie chodzi tylko o to, żeby accuracy wzrosło o kilka punktów
procentowych, ale ważne jest, żeby poprawa była realna i dotyczyła właściwych klas.

Przykładowo, możemy monitorować:

- metryki accuracy, precision, recall, f1-score,
- confusion matrix,
- wyniki dla klas rzadkich (np. weryfikacja auto anotacji najlepszym modelem),
- liczbę przykładów odrzuconych po walidacji,
- zgodność etykiet/przenikanie się klas,
- jakość wygenerowanego języka w zbiorze augmentowanym (LLM).

---

Powrót do [agendy](00_agenda.md).