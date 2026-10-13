#!/usr/bin/env bash
# ================================================================
# Puls Informacji — RadLab News Creator
# Uruchomienie aplikacji Flask / Gunicorn
# ================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# --- Wymagane zmienne środowiskowe (opcjonalne) ---
export PORT="${PORT:-5101}"
export FLASK_DEBUG="${FLASK_DEBUG:-0}"
export CONFIG_PATH="${CONFIG_PATH:-${SCRIPT_DIR}/config/config.json}"

# --- Sprawdź czy Flask jest zainstalowane ---
if ! python3 -m flask --version &>/dev/null; then
    echo "[INFO] Instalowanie zależności..."
    pip3 install --user -q -r "${SCRIPT_DIR}/requirements.txt"
fi

# --- Wyświetl informację ---
echo "================================================="
echo " Puls Informacji by RadLab"
echo "================================================="
echo " Port:       ${PORT}"
echo " Debug:      ${FLASK_DEBUG}"
echo " Config:     ${CONFIG_PATH}"
echo " URL:        http://localhost:${PORT}"
echo "================================================="
echo " Naciśnij Ctrl+C aby zakończyć"
echo "================================================="
echo ""

# --- Uruchom serwer ---
cd "$SCRIPT_DIR"
if command -v gunicorn &>/dev/null; then
    exec gunicorn -w 2 -b "0.0.0.0:${PORT}" app:app
else
    exec python3 app:app
fi
