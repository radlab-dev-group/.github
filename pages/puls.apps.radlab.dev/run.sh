#!/usr/bin/env bash
# ================================================================
# Puls Informacji by RadLab — News Creator
# Skrypt budowania i uruchomienia aplikacji Next.js
# ================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# --- Konfiguracja środowiska ---
export PORT="${PORT:-3000}"

# 1. Konfiguracja zmiennych środowiskowych (.env.local)
if [ ! -f .env.local ] && [ -f .env.example ]; then
    echo "[INFO] Tworzenie .env.local na podstawie .env.example..."
    cp .env.example .env.local
fi

# 2. Instalacja zależności npm
if [ ! -d "node_modules" ]; then
    echo "[INFO] Instalowanie zależności..."
    npm install
fi

# 3. Budowanie produkcyjne aplikacji
echo "[INFO] Budowanie aplikacji produkcyjnej (npm run build)..."
npm run build

# --- Wyświetlenie informacji ---
echo "================================================="
echo " Puls Informacji by RadLab"
echo "================================================="
echo " Port:       ${PORT}"
echo " URL:        http://localhost:${PORT}"
echo "================================================="
echo " Naciśnij Ctrl+C aby zakończyć"
echo "================================================="
echo ""

# 4. Uruchomienie serwera produkcyjnego
exec npm run start -- -p "${PORT}"
