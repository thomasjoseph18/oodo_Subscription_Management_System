# Brightloop subscription management

One platform for plans, quotations, subscriptions, recurring billing, payments and revenue reporting. Built for the Odoo hackathon.

Stack: Django, Django REST Framework, Celery, PostgreSQL, React, Vite, Tailwind CSS.

## Setup

You need Node 20 or later, [uv](https://docs.astral.sh/uv/) and PostgreSQL 15 or later.

Create the database first:

```bash
createdb -U postgres brightloop
```

```bash
cd backend
uv venv --python 3.12
uv pip install -r requirements.txt
cp .env.example .env
.venv/Scripts/python manage.py migrate
.venv/Scripts/python manage.py createsuperuser
.venv/Scripts/python manage.py runserver
```

```bash
cd frontend
npm install
npm run dev
```

The app runs at http://localhost:5173 and the API docs at http://localhost:8000/api/docs/.

Set `DATABASE_URL` in `.env` to your PostgreSQL database. Leave it empty to use SQLite for quick tests only: the database triggers, reporting views and row locks need PostgreSQL. With no `REDIS_URL`, background tasks run inline. With no `EMAIL_HOST_USER`, emails print to the console.

## Background jobs

Needs `REDIS_URL`. On Windows, run the worker with the solo pool:

```bash
.venv/Scripts/celery -A celery_app worker --pool=solo -l info
.venv/Scripts/celery -A celery_app beat -l info
```

## Tests

```bash
cd backend && .venv/Scripts/python -m pytest
cd frontend && npx vitest run
```
