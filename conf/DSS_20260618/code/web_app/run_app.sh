#!/bin/bash

# Skrypt do uruchamiania aplikacji webowej i tworzenia bazy danych jeśli nie istnieje.

PROJECT_ROOT="."
APP_DIR="$PROJECT_ROOT/code/web_app"

echo "Uruchamianie aplikacji webowej..."

# PYTHONPATH aby poprawnie importować moduły
export PYTHONPATH=$PYTHONPATH:$PROJECT_ROOT

# Uruchomienie aplikacji przy użyciu Python 3.10 (z obsługą sqlite3)
python3 "$APP_DIR/app.py"
