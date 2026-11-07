.PHONY: setup dev workers superuser stop

PORT ?= 8000
export PORT

setup:
	@if [ ! -f .env ]; then cp .env.example .env; echo "Creado .env desde .env.example; agrega OMNIROUTE_API_KEY para habilitar la IA."; fi
	uv sync

dev:
	bash scripts/dev.sh

workers:
	bash scripts/dev.sh --workers-only

superuser:
	@set -a; source .env; set +a; uv run python manage.py createsuperuser

stop:
	docker compose down
