.PHONY: dev migrate shell test lint format load-model seed retrain fetch train predict

dev:
	python manage.py runserver

migrate:
	python manage.py migrate

makemigrations:
	python manage.py makemigrations

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

fetch:
	python manage.py fetch_ihsg

train:
	python manage.py train_model

predict:
	python manage.py predict --periods 90

retrain: fetch train predict

fetch-usdidr:
	python manage.py fetch_usdidr

train-usdidr:
	python manage.py train_usdidr

predict-usdidr:
	python manage.py predict_usdidr --periods 90

retrain-usdidr: fetch-usdidr train-usdidr predict-usdidr

retrain-all:
	python manage.py retrain_all

healthcheck:
	curl -s http://localhost:8000/health/
