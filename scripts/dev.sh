#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT="${PORT:-8000}"
MODE="${1:-full}"
cd "$PROJECT_DIR"

if [[ "$MODE" != "full" && "$MODE" != "--workers-only" ]]; then
  echo "Uso: bash scripts/dev.sh [--workers-only]" >&2
  exit 2
fi

if [[ "$MODE" == "full" ]] && (echo >/dev/tcp/127.0.0.1/"$PORT") >/dev/null 2>&1; then
  echo "El puerto ${PORT} ya está ocupado. Usa 'make workers' para arrancar Celery y Beat junto al servidor web existente, o elige otro PORT." >&2
  exit 1
fi

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Creado .env desde .env.example. Agrega OMNIROUTE_API_KEY para habilitar la IA."
fi

set -a
source .env
set +a

if [[ -z "${OMNIROUTE_API_KEY:-}" ]]; then
  echo "OMNIROUTE_API_KEY está vacía; agrega la clave en .env y reinicia make dev para usar la IA."
fi

uv sync
docker compose up -d --wait
uv run python manage.py migrate

children=()
cleanup() {
  trap - EXIT INT TERM
  for pid in "${children[@]}"; do
    kill "$pid" 2>/dev/null || true
  done
  for pid in "${children[@]}"; do
    wait "$pid" 2>/dev/null || true
  done
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

if [[ "$MODE" == "full" ]]; then
  (exec uv run python manage.py runserver "127.0.0.1:${PORT}") &
  children+=("$!")
fi
(exec uv run celery -A config worker -l info -Q celery,matching_v2) &
children+=("$!")
(exec uv run celery -A config beat -l info) &
children+=("$!")

if [[ "$MODE" == "full" ]]; then
  echo "Ramper Job está disponible en http://127.0.0.1:${PORT}/ (Ctrl+C para detener los procesos)."
else
  echo "Worker y Beat están activos. El servidor web existente permanece disponible. (Ctrl+C para detener Worker y Beat)."
fi
wait -n "${children[@]}"
