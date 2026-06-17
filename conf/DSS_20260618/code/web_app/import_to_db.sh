#!/bin/bash

# Skrypt do importu danych z pliku JSONL do bazy danych aplikacji webowej.
# Przykład użycia: ./code/web_app/import_to_db.sh resources/dataset/twitteremo/genailabelled/clarinpl-twitteremo-train-sample-5k_training.jsonl
# Uruchomienie z katalogu projektu (./):
#   bash code/web_app/import_to_db.sh path/to/data.jsonl

IFILE=$1

if [ -z "$IFILE" ]; then
    echo "Użycie: $0 <ścieżka_do_pliku_jsonl>"
    exit 1
fi

echo "Importowanie danych z $IFILE do bazy instance/data.db..."

export PYTHONPATH="$PYTHONPATH:$(pwd)"

python3 "code/web_app/import_data.py" --jsonl "$IFILE"

echo "Import zakończony."
