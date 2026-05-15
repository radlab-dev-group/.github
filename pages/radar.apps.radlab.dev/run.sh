#!/usr/bin/env bash
# ================================================================
# Radar Informacji
# Uruchomienie aplikacji Flask
# ================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# --- Wymagane zmienne środowiskowe (opcjonalne) ---
export PORT="${PORT:-5100}"
export FLASK_DEBUG="${FLASK_DEBUG:-0}"
export CONFIG_PATH="${CONFIG_PATH:-${SCRIPT_DIR}/config/config.json}"

# --- Sprawdź czy Flask jest zainstalowane ---
if ! python3 -m flask --version &>/dev/null; then
    echo "[INFO] Instalowanie zależności..."
    pip3 install --user -q flask requests
fi

# --- Wyświetl informację ---
echo "================================================="
echo " Radar Informacji"
echo "================================================="
echo " Port:       ${PORT}"
echo " Debug:      ${FLASK_DEBUG}"
echo " Config:     ${CONFIG_PATH}"
echo " URL:        http://localhost:${PORT}"
echo "================================================="
echo " Naciśnij Ctrl+C aby zakończyć"
echo "================================================="
echo ""

# --- Uruchom Flask ---
cd "$SCRIPT_DIR"
# --debug "$FLASK_DEBUG"
python3 -m flask --app app run --host 0.0.0.0 --port "$PORT"
