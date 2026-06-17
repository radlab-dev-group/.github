# Augmentacja i labelowanie danych

---

## Augmentacja danych
Proces tworzenia nowych przykładów treningowych na podstawie istniejącego zbioru danych.
Celem nie jest wygenerowanie losowych danych, ale przygotowanie takich przykładów, które:
1. są zgodne z problemem,
2. zachowują poprawną etykietę,
3. zwiększają różnorodność zbioru,
4. pomagają modelowi lepiej generalizować,
5. uzupełniają braki w klasach gorzej reprezentowanych.

W przypadku danych tekstowych augmentacja może polegać między innymi na:
- parafrazowaniu istniejących przykładów,
- zmianie stylu wypowiedzi,
- generowaniu przykładów krótszych lub dłuższych,
- tworzeniu wariantów formalnych i nieformalnych,
- dodawaniu literówek lub potocznego języka,
- generowaniu przykładów dla klas rzadkich,
- tworzeniu trudniejszych przypadków granicznych.

**Przykład:**

Dane wejściowe:
```text
„Chcę zwrócić zamówiony produkt, ponieważ nie spełnia moich oczekiwań.”
```

Etykieta: `zwrot`

Przykłady po augmentacji:

```text
„Jak mogę odesłać zakupiony towar?”
„Produkt mi nie odpowiada i chciałbym go zwrócić.”
„Czy da się zrobić zwrot zamówienia?”
„Towar nie jest taki, jak oczekiwałem. Proszę o informację, jak go oddać.”
```

Wszystkie te przykłady powinny nadal należeć do tej samej klasy: `zwrot`.

---

## Labelowanie danych z wykorzystaniem LLM

Proces przypisywania etykiet przykładom w istniejacym zbiorze danych. W przypadku problemu klasyfikacji oznacza to, 
że dla każdego przykładu określamy klasę, do której ten przykład należy.

Przykładowo, jeśli mamy tekst:
```text
„Znowu wszystko działa fatalnie, mam już dość.”
```
możemy przypisać mu etykietę: `negatywna`

W klasycznym podejściu takie etykiety nadaje człowiek - annotator, ekspert domenowy albo zespół osób odpowiedzialnych
za przygotowanie danych. Jest to jednak proces czasochłonny, kosztowny i trudny do skalowania, szczególnie 
gdy mamy tysiące lub miliony przykładów.  W podejściu z wykorzystaniem LLM-a model generatywny pomaga wstępnie 
oznaczać dane. Nie traktujemy go jednak jako nieomylnego źródła prawdy, ale jako narzędzie wspierające człowieka.

Labelowanie z wykorzystaniem LLM-a jest szczególnie przydatne, gdy:
- mamy dużo nieoznaczonych danych,
- chcemy szybko przygotować pierwszy zbiór treningowy,
- potrzebujemy wstępnych etykiet do eksperymentów,
- chcemy ograniczyć koszt ręcznej anotacji,
- człowiek ma raczej sprawdzać i poprawiać niż oznaczać wszystko od zera,
- klasy są opisowe i można je jasno zdefiniować w promptach.

Trzeba jednak pamiętać, że etykiety nadane przez LLM są tylko propozycjami. Model może się mylić, 
zwłaszcza przy tekstach ironicznych, niejednoznacznych, pozbawionych kontekstu albo zawierających slang. 

> LLM nie zastępuje całkowicie człowieka w anotowaniu danych. Przyspiesza przygotowanie etykiet, a człowiek koncentruje się na kontroli jakości, poprawianiu błędów i rozstrzyganiu przypadków trudnych.
