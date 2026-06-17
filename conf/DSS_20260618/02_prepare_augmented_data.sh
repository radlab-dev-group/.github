#!/bin/bash

# ----------------------------------------------------------------------------------------------------------------------
# Dla "testu" sprawdzamy jaka jest jakoś labelowania
# za pomocą oss120b (i aktualną wersją prompta) względem ręcznego datasetu
bash code/augmentation/01_label_with_genai.sh

# ----------------------------------------------------------------------------------------------------------------------
# Przygotowanie zbioru augmentowanego - selekcja klas do augmentacji
#  - na podstawie rozkładu klas decydujemy - "za mało przypadków dla `pozytywny`"
bash code/augmentation/02_select_class_to_augmentation.sh

# ----------------------------------------------------------------------------------------------------------------------
# Uruchamianie augmentacji danych bazując na samplu 5k przykładów train
#  - augmentujemy nowe przypadki dla `pozytywny` na podstawie przykładów tej klasy
bash code/augmentation/03_examples_augemntation.sh
