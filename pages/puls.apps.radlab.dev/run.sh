#!/usr/bin/env bash
# ================================================================
# Puls Informacji by RadLab — News Creator (Flask Edition)
# Uruchomienie aplikacji Flask
# ================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# --- Wczytaj zmienne ze środowiska lub .env ---
if [ -f .env ]; then
    set -a
    # shellcheck disable=SC1091
    source .env
    set +a
fi

export PORT="${PORT:-5200}"
export FLASK_DEBUG="${FLASK_DEBUG:-0}"

# --- Sprawdź czy zależności są zainstalowane ---
if ! python3 -m flask --version &>/dev/null; then
    echo "[INFO] Instalowanie zależności Pythona..."
    pip3 install --user -q -r requirements.txt || pip install --user -q -r requirements.txt
fi

# --- Wyświetl informację ---
echo "================================================="
echo " Puls Informacji by RadLab (Flask App)"
echo "================================================="
echo " Port:       ${PORT}"
echo " Debug:      ${FLASK_DEBUG}"
echo " URL:        http://localhost:${PORT}"
echo "================================================="
echo " Naciśnij Ctrl+C aby zakończyć"
echo "================================================="
echo ""

# --- Uruchom serwer produkcyjny (Gunicorn) lub developerski (Flask) ---
if [ "${FLASK_DEBUG}" = "1" ]; then
    exec python3 -m flask --app app run --host 0.0.0.0 --port "${PORT}"
else
    exec gunicorn -w 4 -b "0.0.0.0:${PORT}" app:app
fi
