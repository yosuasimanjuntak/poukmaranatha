# poukmaranatha

Django + HTMX + Tailwind + Alpine starter.

## Stack

- Django 5.2 on Python 3.14
- HTMX (`django-htmx` middleware + vendored `htmx.min.js`)
- Tailwind CSS 4 via `django-tailwind` (Node pipeline)
- Alpine.js (vendored)
- SQLite for dev, PostgreSQL for prod (via `dj-database-url`)
- WhiteNoise for static files in prod
- pytest-django, ruff, pre-commit

## Quickstart

Requires Python 3.14, Node 20+, and `npm` on PATH.

```powershell
# 1. Virtualenv + Python deps
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements/dev.txt

# 2. Env
Copy-Item .env.example .env
# (edit .env: set DJANGO_SECRET_KEY)

# 3. Tailwind / Alpine / HTMX assets
python manage.py tailwind install
python manage.py tailwind build

# 4. Database
python manage.py migrate
python manage.py createsuperuser   # optional

# 5. Pre-commit (one-time)
pre-commit install
```

## Run

Two terminals — one for the Tailwind watcher, one for Django:

```powershell
python manage.py tailwind start    # terminal 1: rebuild CSS on change
python manage.py runserver         # terminal 2: Django dev server
```

Visit <http://127.0.0.1:8000/>. The home page exercises Tailwind, HTMX, and Alpine.

## Project layout

```
config/                Django project (settings split: base / dev / prod)
apps/
  core/                Home view, HTMX demo
  accounts/            Reserved for future auth customization
templates/             Project-level templates (base, registration, errors)
theme/                 django-tailwind theme app
  static_src/          Tailwind + npm sources
  static/              Compiled CSS + vendored htmx.min.js, alpine.min.js
static/                Project-level static files (added to STATICFILES_DIRS)
requirements/          Split requirements: base / dev / prod
```

## Tests + lint

```powershell
ruff check .
ruff format --check .
pytest
```

## Production

See **[DEPLOYMENT.md](DEPLOYMENT.md)** for a full step-by-step deploy to Ubuntu (fresh install + update flow). Reference deployment lives at https://poukmaranatha.ionyx.org.
