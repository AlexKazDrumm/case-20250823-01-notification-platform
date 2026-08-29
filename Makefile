.PHONY: init migrate run celery worker beat test lint

init:
	python -m venv .venv && . .venv/bin/activate && pip install -U pip && pip install -r requirements.txt

migrate:
	. .venv/bin/activate && python manage.py makemigrations && python manage.py migrate

run:
	. .venv/bin/activate && python manage.py runserver 0.0.0.0:8000

worker:
	. .venv/bin/activate && celery -A app worker -l info

beat:
	. .venv/bin/activate && celery -A app beat -l info --pidfile=

test:
	. .venv/bin/activate && python manage.py test
