.PHONY: install backend test format lint

install:
	python -m venv .venv && . .venv/bin/activate && pip install -r backend/requirements.txt

backend:
	cd backend && python manage.py runserver

test:
	cd backend && pytest -q

format:
	black backend
	isort backend

lint:
	black --check backend
	isort --check backend
