.PHONY: dev migrate shell test lint format

dev:
	python manage.py runserver

migrate:
	python manage.py migrate

shell:
	python manage.py shell

test:
	python manage.py test

lint:
	ruff check .

format:
	ruff format .

load-model:
	python manage.py load_model
