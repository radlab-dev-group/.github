# Prezentacja DSS 2026

Zawartość _presentation_ powstała w ramach prezentacji przygotowanej na
**DSS 2026 Tutorials — Augmentacja danych uczących dla modeli klasyfikacyjnych z wykorzystaniem lokalnych LLMów**.

## Struktura

| Podkatalog     | Opis                                                                                                  |
|----------------|-------------------------------------------------------------------------------------------------------|
| [md/](md/)     | Opis procesu, instrukcje itd. w Markdown (każdy plik = sekcja w prezentacji)                          |
| [pptx/](pptx/) | Szablon PowerPoint prezentacji (`.pptx`) oraz skrypt generujący slajdy na podstawie opisów w Markdown |
| [imgs/](imgs/) | Obrazki/wykresy użyte w prezentacji (macierze pomyłek, rozkłady klas itp.)                            |

## Slajdy

Prezentacja składa się z następujących sekcji:

1. **Agenda** — overview całości procesu
2. **Wstęp** — kontekst teoretyczny i praktyczny
3. **Augmentacja i labelowanie** — techniki augmentacji, HITL, active learning loop
4. **Technikalia** — sprzęt, instalacja, LLM router, labelowanie, augmentacja
5. **Wnioski** — podsumowanie i wnioski
6. **Uczenie** — szczegóły procesu uczenia modelu

## Generowanie PowerPoint

Pierwsza wersja PowerPoint została wygenerowana na podstawie plików Markdown:

```bash
cd pptx
python generate_pptx_from_md_dss2026.py
```
