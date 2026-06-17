#!/bin/bash

# Skrypt do uruchamiania aplikacji webowej przez Gunicorn.

PROJECT_ROOT="."
APP_DIR="$PROJECT_ROOT/code/web_app"

echo "Uruchamianie aplikacji webowej przez Gunicorn..."

# PYTHONPATH aby poprawnie importować moduły
export PYTHONPATH=$PYTHONPATH:$PROJECT_ROOT

# Uruchomienie aplikacji przy użyciu Gunicorn
CUDA_VISIBLE_DEVICES=0 gunicorn --bind 0.0.0.0:5000 --workers 2 --threads 4 "code.web_app.app:app"
