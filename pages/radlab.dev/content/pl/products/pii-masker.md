---
title: "PII Masker"
subtitle: "Wielowarstwowa anonimizacja i ochrona danych osobowych w systemach sztucznej inteligencji"
slug: "pii-masker"
description: "PII Masker to zaawansowany silnik ochrony prywatności łączący deterministyczne reguły z walidacją sum kontrolnych (FastMasker) oraz model uczenia maszynowego NER (anonymizer-model). Skutecznie wykrywa i maskuje PESEL, NIP, karty płatnicze, adresy i dane wrażliwe przed wysłaniem promptów do modeli językowych."
icon: "shield"
status: "Open Source · Apache-2.0"
version: "v1.1"
tags: ["PII Masking", "Data Privacy", "NER Model", "FastMasker", "RODO / GDPR", "LLM Security"]
actions:
  - {label: "Tester online (masker.apps)", href: "https://masker.apps.radlab.dev/anonymize/", style: primary}
  - {label: "GitHub: anonymizer-model", href: "https://github.com/radlab-dev-group/anonymizer-model", style: quiet}
  - {label: "GitHub: fast_masker plugin", href: "https://github.com/radlab-dev-group/llm-router-plugins/tree/main/llm_router_plugins/maskers/fast_masker", style: quiet}
---

## Dlaczego ochrona PII w systemach AI jest kluczowa?

Wysyłanie zapytań użytkowników i dokumentów firmowych do zewnętrznych modeli chmurowych niesie ryzyko **wycieku informacji poufnych i naruszenia przepisów RODO/GDPR**. 

Tradycyjne wyrażenia regularne często generują dużą liczbę fałszywych alarmów (false positives) lub pomijają nietypowo sformatowane dane osobowe. Z kolei modele czysto neuronowe mogą mieć trudności z precyzyjną weryfikacją cyfrowych identyfikatorów z sumami kontrolnymi.

**PII Masker** rozwiązuje ten problem poprzez **architekturę hybrydową**: łączy deterministyczny silnik regułowy o ścisłym priorytecie z modelem rozpoznawania jednostek nazwanych (NER) wytrenowanym dla specyfiki języka polskiego.

---

## Architektura dwuwarstwowa

<div class="product-flow">
  <div class="product-flow-endpoint">Surowy tekst z danymi wrażliwymi</div>
  <ol class="product-flow-steps">
    <li>
      <h3>1. FastMasker</h3>
      <p>Silnik deterministyczny i walidacja sum kontrolnych: PESEL, NIP, REGON, IBAN, karty płatnicze i VIN. Reguły formatów: e-mail, IPv4/IPv6, URL, telefony i kody pocztowe.</p>
    </li>
    <li>
      <h3>2. Anonymizer Model</h3>
      <p>Model Transformer NER dla języka polskiego: imiona, nazwiska, nazwy własne i stanowiska, a także adresy, lokalizacje i kontekst nieregularny.</p>
    </li>
  </ol>
  <div class="product-flow-endpoint">Zanonimizowany tekst z tokenami zastępczymi, np. <code>{{PESEL}}</code>, <code>{{CREDIT_CARD}}</code></div>
</div>

---

## Moduły składowe

### 1. FastMasker: Błyskawiczny silnik regułowy

Moduł `fast_masker` aplikuje reguły w ściśle określonym porządku — od identyfikatorów o **najwyższej pewności (z walidacją sum kontrolnych)** do wzorców ogólnych:

* **Identyfikatory weryfikowane sumami kontrolnymi:**
  * **Karty kredytowe (`CreditCardRule`):** Walidacja algorytmem Luhna (13–19 cyfr) → `{{CREDIT_CARD}}`
  * **Numery VIN (`VinRule`):** Walidacja sumy kontrolnej ISO 3779 (pozycja 9) → `{{VIN}}`
  * **PESEL (`PeselTaggedRule` i `PeselRule`):** Weryfikacja cyfry kontrolnej PESEL oraz daty urodzenia → `{{PESEL}}`
  * **NIP i REGON (`NipRule`, `RegonRule`):** Algorytmy wagowe dla polskich identyfikatorów podatkowych i rejestrowych → `{{NIP}}`, `{{REGON}}`
  * **Rachunki bankowe (`IbanRule`, `NrbRule`):** Standard NRB (26 cyfr) i międzynarodowy IBAN z algorytmem modulo 97 → `{{IBAN}}`
  * **Dokumenty tożsamości:** Polski Dowód Osobisty (`IdCardNumberRule`) i Paszport (`PassportNumberRule`) → `{{ID_CARD}}`, `{{PASSPORT}}`
  * **Identyfikatory techniczne:** Adresy MAC, numery seryjne SIM ICCID, certyfikaty SSL, tokeny JWT → `{{MAC_ADDRESS}}`, `{{JWT}}`
* **Identyfikatory wzorcowe i telekomunikacyjne:**
  * Adresy e-mail → `{{EMAIL}}`
  * Adresy IPv4 i IPv6 → `{{IP_ADDRESS}}`
  * Adresy URL i domeny → `{{URL}}`
  * Polskie i międzynarodowe numery telefonów → `{{PHONE}}`
  * Kody pocztowe, tablice rejestracyjne, kwoty pieniężne i daty

### 2. Anonymizer Model: Model NER dla języka polskiego

Dla danych, których nie da się jednoznacznie opisać sumami kontrolnymi (imiona, nazwiska, nazwy ulic, kontekstowe dane adresowe), udostępniamy model **`anonymizer-model`**:

* **Architektura:** `AutoModelForTokenClassification` oparta na architekturze RoBERTa zoptymalizowanej pod kątem języka polskiego.
* **Trening na korpusach anotowanych:** Zbiory takie jak `clarin-pl/kpwr-ner` ze zgeneralizowaną mapą etykiet.
* **Zaawansowany post-processing:** Algorytm scalania sub-tokenów (sub-token merging), zachowywanie interpunkcji i spacji oraz precyzyjne odzyskiwanie granic słów.
* **Wydajność:** Opcja kwantyzacji dynamicznej (ONNX / INT8) umożliwiająca wnioskowanie na CPU bez konieczności angażowania drogich kart graficznych.

---

## Integracja z LLM Router

PII Masker działa jako natywna wtyczka w potoku **LLM Routera**:

1. **Pre-inference:** Gdy użytkownik wysyła prompt, Masker podmienia dane wrażliwe na jednoznaczne tokeny zastępcze.
2. **Inference:** Model językowy (np. w chmurze) przetwarza tekst bez dostępu do prawdziwych danych osobowych.
3. **Post-inference (Opcjonalnie):** W razie potrzeby LLM Router może bezpiecznie przywrócić oryginalne wartości w tekście wyjściowym przed zwróceniem go do autoryzowanego użytkownika.

---

## Przykładowe użycie w Pythonie

```python
from llm_router_plugins.maskers.fast_masker import FastMasker, ALL_RULES

# Inicjalizacja maskera z pełnym zestawem reguł
masker = FastMasker(rules=ALL_RULES)

tekst = (
    "Klient Jan Kowalski, PESEL: 44051401359, opłacił fakturę kartą "
    "4532 1234 5678 9010 na kwotę 1 250,00 PLN. "
    "Kontakt: jan.kowalski@firma.pl lub +48 601 234 567."
)

zanonimizowany = masker.mask(tekst)
print(zanonimizowany)
# Wynik:
# Klient Jan Kowalski, {{PESEL_TAGGED}}, opłacił fakturę kartą
# {{CREDIT_CARD}} na kwotę {{MONEY}}.
# Kontakt: {{EMAIL}} lub {{PHONE}}.
```

---

## Zasoby i repozytoria

* **Tester online:** [masker.apps.radlab.dev/anonymize/](https://masker.apps.radlab.dev/anonymize/)
* **Repozytorium modelu NER:** [radlab-dev-group/anonymizer-model](https://github.com/radlab-dev-group/anonymizer-model)
* **Repozytorium silnika regułowego:** [radlab-dev-group/llm-router-plugins](https://github.com/radlab-dev-group/llm-router-plugins)
* **Licencja:** Apache 2.0 (Open Source)
