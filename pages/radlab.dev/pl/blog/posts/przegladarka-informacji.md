---
title: "Przeglądarka informacji"
date: 2025-05-28
updated: 2025-09-26
slug: przegladarka-informacji
description: "Z perspektywy marketingowej, dobrze byłoby zacząć ten wpis w stylu: Dzisiaj przedstawiamy rewolucyjne, w pełni zautomatyzowane rozwiązanie, które w czasie…"
tags: ["playground"]
categories: ["ciekawostki", "eksperyment", "embedding", "GenAI", "model", "narzędzia", "transformatory"]
image: media/przegladarka-informacji/_featured.avif
lang: pl
wp_id: 3113
---

Z perspektywy marketingowej, dobrze byłoby zacząć ten wpis w stylu:

> *Dzisiaj przedstawiamy rewolucyjne, w pełni zautomatyzowane rozwiązanie, które w czasie „rzeczywistym” pozwoli Ci analizować trendy w mediach. Chcesz się dowiedzieć o czym się pisze? Co jest na topie? Tak! Dobrze trafiłeś, to właśnie dzisiaj masz okazję skorzystać….*

Easy…. Takie trochę Telemango w dzisiejszych czasach… nie wypada tak 😉 Także zaczniemy standardowo.

![](@media/przegladarka-informacji/01-image-3.avif)

## O czym jest dzisiejszy wpis?

Na [playgroundzie](https://playground.radlab.dev/) udostępniliśmy nową funkcjonalność, nazwaliśmy ją [Przeglądarka Informacji](https://playground.radlab.dev/news_browser) i służy dokładnie do tego, jak się nazywa — czyli przeglądania informacji w czasie.

> Czym jest **informacja**? Jako informację rozumiemy **zwartą** **grupę** **tematyczną** newsów ze stron internetowych, które w domyśle dotyczą tej samej sytuacji/tematu/zdarzenia… Tego, co pojawia się w wiadomościach, o czym piszą media, co jest na topie. To, co w danym dniu/przedziale czasowym jest tym, o czym się czyta, tylko zebrane w jednym miejscu, podsumowane i nazwane. **Nazwa** informacji **nie** **jest** w żadnym stopniu **predefiniowana**, **jest** **wyznaczana** **na** **podstawie** pojawiających się **newsów** powiązanych w zwarte grupy informacyjne. Nazwa informacji codziennie może być inna — zależy o czym się pisze (i czyta ;-)).

Podstawą działania *Przeglądarki*, są informacje występujące na popularnych serwisach newsowych, które cyklicznie analizujemy i wyniki tych analiz prezentujemy w *piaskownicy*. *Przeglądarka* prezentuje proces automatycznej analizy informacji z tych serwisów. Jest mechanizmem, który przedstawia najistotniejsze informacje z danego dnia, nazwie te informacje oraz napisze krótkie streszczenie, w którym można dowiedzieć się w skrócie czego dotyczy wykryta informacja. Oprócz tego, przedstawi szereg powiązanych (nazwijmy to) *wyzwalaczy* tej informacji:

- poda dokładne adresy do stron internetowych, które o tej informacji piszą;
- pokaże źródła propagacji informacji za pomocą diagramu z wizualizacją procentowego udział konkretnego portalu w udostępnianiu tej informacji;
- przedstawi analizę polaryzacji tej informacji (warto zwrócić uwagę na korelację nazwy informacji z polaryzacją informacji);
- za pomocą kalendarza umożliwi śledzenie i analizę informacji w czasie (aczkolwiek może być ona różnie nazwana);

## Jak to działa?

Od strony technicznej, jest to mix różnych metod i optymalizacji. Mechanizm bada różnice między tekstami i na podstawie ich podobieństwa dobiera do jednej grupy informacyjnej te newsy, które z perspektywy zredukowanego embeddingu są do siebie najbardziej podobne. Mechanizm wydzielania skupisk informacyjnych dostraja swoje działanie do liczby danych, które analizuje. Są dni, w których pojawia się około 600 newsów, ale są również dni, kiedy pojawia się dwa razy więcej. Mechanizm na podstawie wielu rozkładów dobiera taki, który najlepiej wpasowuje się w dodatkowe warunki podziału danych, np. nie pozwala na podziały poniżej 5 grup informacyjnych oraz na powyżej 60, a dodatkowo uwzględnia *złoty środek* czyli celowanie w 20 tematów dziennie, a jednocześnie optymalizuje liczbę przykładów odrzucanych. Z perspektywy *Przejrzanych* dwóch miesięcy, najczęściej w mediach pojawia się od 20 do 30 informacji dziennie.

## Dla kogo: od Sasa do lasa

Można powiedzieć: Od Sasa do lasa… Z perspektywy osoby poszukujących pewnych informacji, jest to rozwiązanie, które w jednym miejscu pozwala dotrzeć do dziesiątek czy setek newsów z konkretnego dnia z konkretną informacją. Jeżeli interesują kogoś wydarzenia sportowe, a danego dnia pojawiło się odpowiednio dużo informacji z wydarzeń sportowych, to dostanie podsumowanie wielu wydarzeń (w tym również z zagranicznych źródeł). Przykładowo propozycja numer 1 (domyślnie pojawia się numer 0) w dniu 26.05.2025 pojawia się informacja „*Sport – sukcesy i zmiany.*„, której podsumowanie wygląda tak (klik aby powiększyć):

![](@media/przegladarka-informacji/02-image-5.avif)

A dodatkowo dostajemy adresy powiązanych stron z informacją z tym opisem:

{{< details title="Kliknij aby zobaczyć zdjęcie" >}}

![](@media/przegladarka-informacji/03-image-16.avif)

{{< /details >}}

Zaś z perspektywy analityka, powiązanie informacji odnośnie źródeł propagacji, czyli wykres:

![](@media/przegladarka-informacji/04-image-14.avif)

pokazuje skąd ta informacja przychodzi i na ile zdominowana jest przez jedno źródło danych. I o ile w przypadku sportu, może to być mniej istotna zmienna, o tyle w informacjach związanych np. z polityką czy nowoczesnymi technologiami, rozkład pochodzenia stron może pokazywać proces wprowadzania informacji w obieg. Zaś analiza tej informacji w czasie za pomocą kalendarza, umożliwia śledzenie jej i umożliwia wyciąganie wniosków. Należy jedynie pamiętać, że informacje nazywane są indywidualnie w perspektywie jednego dnia, dlatego nazwy mogą się różnić w zależności od dnia. Dlatego (jeszcze) wymagana jest ludzka interakcja, aby śledzić konkretną informację w czasie 😉 Dodatkowo otrzymujemy podsumowanie na temat rozkładu polaryzacji emocji w postaci diagramu:

![](@media/przegladarka-informacji/05-image-15.avif)

Przy analizie takiego diagramu warto zwrócić uwagę na korelację nazwy informacji z polaryzacją/wydźwiękiem tekstu (informacja *pozytywna*, *negatywna*, *neutralna*). Nazwa kategorii bardzo wskazuje jaki może być rozkład polaryzacji. A za wykrycie polaryzacji odpowiada nasz model, który na *[playgroundzie](https://playground.radlab.dev/)* działa od bardzo dawna i służy do oceny tekstów w czasie rzeczywistym. Właśnie na podstawie decyzji tego modelu przedstawiony jest udział konkretnego wydźwięku w konkretnej informacji (nie jest to wydźwięk artykułu podsumowującego, a newsów z informacją). Oprócz tego dostajemy dokładne dane dotyczące informacji odnośnie liczby newsów:

![](@media/przegladarka-informacji/06-image-13.avif)

A powiązanie liczby newsów w informacji z liczbą newsów w całym dniu (a do tej zmiennej jest dostęp):

![](@media/przegladarka-informacji/07-image-10.avif)

pozwala określić istotność informacji w kontekście całego dnia…. Resztę można zostawić wyobraźni 😉

## Outro

Dlaczego tylko jeden dzień? Nie ma problemu, mechanizm działa w oparciu o przedziały czasowe, analizuje informacje ze wskazanego przedziału, nie na wskazany dzień. Sam mechanizm jest uniwersalny i do analiz ponadtygodniowych wymaga już nieco mocniejszego sprzętu (i o dziwo jest to RAM i procesor, nie gpu :)), analiza około tysiąca newsów z dnia trwa od 15 do 28 minut, więc nie tak długo. Aktualnie analizujemy dni aż do 01.01.2025, po tym procesie można będzie prześledzić informacje od 01.01.2025 do dnia, w którym będzie się śledziło 😉 Mechanizm działa w oparciu o zautomatyzowane jednodniowe analizy, dlatego codziennie pojawia się podsumowanie informacji z dnia wcześniejszego. Po analizie jednodniowej planujemy wprowadzić właśnie analizy tygodniowe.

Zachęcamy do *[Przeglądania Informacji](https://playground.radlab.dev/news_browser)*, analizowania i wyciągania wniosków. Przeglądarka jest oczywiście w całości non-profit, bez reklam i logowania się 😉

{{< details title="Content Supervisor o Przeglądarce [klik]" >}}

Podsumowanie tego wpisu za pomocą content supervisora z [Czatu Publicznego](https://playground.radlab.dev/Czat_publiczny) 😉 Oto, co gemma napisała o *[Przeglądarce](https://playground.radlab.dev/Przegl%C4%85darka_Informacji)*:

![](@media/przegladarka-informacji/08-image-9.avif)

Rozmowa do przeczytania na [Czacie Publicznym](https://playground.radlab.dev/Czat_publiczny), wystarczy załadować hash:

> ```text
> 7ivUpPCTNPR0d8gGbPT9hh5nD1Y8yMapJSOISOTg7mFJvryf3BgzGdT03Bsf0Ui3gWymAkciIWRxPJnHslFwnP0FtYzrSi8xj7AOqxT5lcqQ1waaYadNUIOoOJAqu9wP
> ```

{{< /details >}}

---

> **Sprawdź powiązane rozwiązania:** Zobacz pełny 8-etapowy potok przetwarzania i architekturę w opisie [Radar Informacji](/products/radar/) oraz przetestuj wersję demonstracyjną na żywo w [RDL Playground AI](/products/playground/).
