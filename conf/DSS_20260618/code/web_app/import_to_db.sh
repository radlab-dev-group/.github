#!/bin/bash

# Skrypt do importu danych z pliku JSONL do bazy danych aplikacji webowej.
# Przykład użycia: ./import_to_db.sh resources/dataset/twitteremo/genailabelled/clarinpl-twitteremo-train-sample-5k_training.jsonl

IFILE=$1

if [ -z "$IFILE" ]; then
    echo "Użycie: $0 <ścieżka_do_pliku_jsonl>"
    exit 1
fi

# Ścieżka do bazy danych (absolutna dla pewności)
#DB_PATH="${`pwd`}/code/web_app/data.db"
PROJECT_ROOT="code"

echo "Importowanie danych z $IFILE do bazy data.db..."
#
export PYTHONPATH=$PYTHONPATH:$PROJECT_ROOT

/usr/bin/python3.10 "code/web_app/import_data.py" \
    --jsonl "$IFILE"

echo "Import zakończony."
