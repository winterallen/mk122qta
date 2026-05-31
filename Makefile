.PHONY: sync test test-unit test-e2e check format dev docs docker

sync:
	uv sync

test:
	uv run pytest

test-unit:
	uv run pytest -m "not integration and not e2e"

test-e2e:
	uv run pytest -m e2e

check:
	uv run ruff check packages apps tests
	uv run ruff format --check packages apps tests
	uv run mypy packages apps

format:
	uv run ruff format packages apps tests
	uv run ruff check --fix packages apps tests

dev:
	docker compose up -d nats redis prometheus grafana minio mlflow

docs:
	uv run mkdocs serve

docker:
	docker build -t $(IMAGE) .
