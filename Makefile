.PHONY: install backend test format lint

install:
\tpython -m venv .venv && . .venv/bin/activate && pip install -r backend/requirements.txt

backend:
\tcd backend && python manage.py runserver

test:
\tpytest -q

format:
\tblack .
\tisort .

lint:
\tblack --check .
\tisort --check .
