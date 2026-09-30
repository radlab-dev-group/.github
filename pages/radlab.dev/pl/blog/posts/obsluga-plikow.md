---
title: "Obsługa plików"
date: 2021-06-22
updated: 2024-04-27
slug: obsluga-plikow
description: "W jaki sposób mogę pakować/rozpakowywać katalogi z bardzo dużą liczbą…"
categories: ["ciekawostki"]
image: media/obsluga-plikow/_featured.png
lang: pl
wp_id: 2029
---

### W jaki sposób mogę pakować/rozpakowywać katalogi z bardzo dużą liczbą plików:

Pierwszym ze sposobów jest wykorzystanie 7zipa (**7z**) wraz z uruchomieniem go w trybie wielowątkowym. Jeżeli nie zależy nam na kompresji, a jedynie na czasie kompresowania:

`time 7z a -tzip -mx=11 -mmt=on plik.zip katalog_z_wieloma_plikami`

Powyższe polecenie uruchomi pakowanie katalogu `katalog_z_wieloma_plikami` na 11 wątkach (`-mx=11` oraz `-mmt=on`) z kompresją **zip**.

### W jaki sposób mogę podzielić plik na N części bez łamania linii

`split -n l/2 input_file prefix_name`

powyższa komenda podzieli plik `input_file` na `N=2` częsci, a dwa nowe pliki będą posiadały prefix `prefix_name`
