.PHONY: dev migrate seed test test-api test-ai test-regression lint

dev:
	uvicorn backend.app.main:app --reload

migrate:
	alembic -c backend/alembic.ini upgrade head

seed:
	python -m backend.scripts.seed

test:
	pytest

test-api:
	pytest -m api

test-ai:
	pytest -m ai

test-regression:
	pytest -m regression

lint:
	ruff check backend tests

