# poukmaranatha — CLAUDE.md

Church ministry scheduling app for an Indonesian-speaking congregation. Replaces the WhatsApp-and-spreadsheets workflow with a mobile-first web app where volunteers see their next assignment in under three seconds and admins fill empty slots in under five minutes.

Live deployment: https://poukmaranatha.ionyx.org

---

## Tech stack

| Layer | Choice |
|---|---|
| Backend | Django 5.2, Python 3.14 |
| Frontend | HTMX (django-htmx), Alpine.js, Tailwind CSS 4 (django-tailwind) |
| DB | SQLite (dev), PostgreSQL 16 (prod) |
| Static | WhiteNoise + CompressedManifestStaticFilesStorage |
| Assets | Node 20 pipeline in `theme/static_src/` |
| Fonts | Inter variable, self-hosted at `theme/static/vendor/` |
| Prod server | Gunicorn + nginx + systemd on Ubuntu 24.04 (DigitalOcean) |
| Tests | pytest-django |
| Lint | ruff |

---

## Project layout

```
config/                  Django project
  settings/base.py       Shared settings (imported by dev.py and prod.py)
  settings/dev.py
  settings/prod.py
  urls.py                Root URL conf
apps/                    All Django apps (added to sys.path, so no "apps." prefix in imports)
  accounts/              Custom User model, roles, middleware, management commands
  ministry/              Core domain: Pelayanan, Schedule, Assignment, Kolekte
  core/                  Home view, HTMX demo
templates/               Project-level templates
  base.html
  registration/          Login/logout
  core/                  Home
  ministry/              All scheduling UI
  accounts/              User management
  components/            top_bar, bottom_tabs, toast, spinner, language_switcher
theme/                   django-tailwind theme app
  static_src/            Tailwind source + npm (postcss, Inter font download)
  static/                Compiled CSS + vendored htmx.min.js, alpine.min.js
locale/                  .po/.mo translation files (id and en)
deploy/                  nginx conf, gunicorn conf, systemd unit, env example
scripts/update.sh        One-command deploy script (git pull → pip → npm → migrate → collectstatic → compilemessages → restart)
requirements/
  base.txt               Django, django-htmx, django-tailwind, django-environ, dj-database-url, whitenoise, Pillow
  dev.txt                + pytest-django, django-browser-reload, pre-commit
  prod.txt               + gunicorn, psycopg
```

---

## Domain model (apps/ministry/)

- **Pelayanan** — a worship-service category (e.g. Umum, Sekolah Minggu). Has a `role_slots` lineup.
- **UserRole** — a ministry position (e.g. Worship Leader, Drum). Users can hold multiple roles.
- **PelayananRoleSlot** — template: how many of a given UserRole a Pelayanan needs.
- **RecurrenceRule** — frequency (daily/weekly/monthly), date range, time; generates Schedule instances via `expand_recurrence()`.
- **Schedule** — a concrete service instance (Pelayanan + start_at). Has `assignments`.
- **Assignment** — one role slot for one Schedule; `user` is nullable (empty = unfilled).
- **Kolekte** — offering/collection record tied to one Schedule. Fields: `type` (free text, e.g. "Kolekte", "Kotak Pembangunan"), `total` (IDR integer), `notes`, `recorded_by` (FK to User). Shown as an HTMX section at the bottom of every schedule detail page. CRUD at `/schedules/<pk>/kolekte/`, `/kolekte/<pk>/edit/`, `/kolekte/<pk>/delete/`.

Service layer (`apps/ministry/services.py`):
- `expand_recurrence(rule)` — expands a RecurrenceRule into Schedule rows + materializes assignments.
- `materialize_assignments(schedule)` — creates empty Assignment rows from Pelayanan's role slots. Idempotent.
- `create_one_off_schedule(...)` — creates a single Schedule + assignments.

## User model (apps/accounts/)

Custom `User` extends `AbstractUser` with:
- `full_name`, `photo`, `language` (default `"id"`)
- `account_role`: `superuser` | `admin` | `viewer` (drives `is_staff`/`is_superuser` on save)
- `pelayanan_categories` M2M to `ministry.Pelayanan` — which worship service types this person can be assigned to (Umum, Sekolah Minggu, Pemuda, Wanita, Lansia, Remaja). The assignment picker filters candidates by this field against the schedule's Pelayanan.
- `user_roles` M2M to `ministry.UserRole` — controls which role slots a user appears in when assigning. Shown in user form below `pelayanan_categories`.

Assignment picker filtering: candidates must match **both** the slot's `user_role` **and** the schedule's `pelayanan` via `pelayanan_categories`. A person only appears in the Umum picker if Umum is in their `pelayanan_categories`.

Permission helpers in `apps/accounts/permissions.py`:
- `is_admin_or_above(user)` — function used in views
- `AdminOrAboveRequiredMixin` — for class-based views

Context processor `accounts.context_processors.account_role` injects `account_role` into all templates.

`UserLanguageMiddleware` reads `request.user.language` and activates the correct translation.

Management commands:
- `seed_superusers` — creates `aamsa` and `yosua` from env vars (`DJANGO_SUPERUSER_AAMSA_PASSWORD`, `DJANGO_SUPERUSER_YOSUA_PASSWORD`). Idempotent.
- `import_users` — bulk-import users from a CSV file (`users_import_template.csv` in project root). Columns: `full_name`, `username`, `password`, `account_role`, `language`, `user_roles` (pipe-separated). Re-running updates roles; passwords not overwritten unless `--reset-passwords`.
- `import_legacy_csv <csv_dir>` — one-shot migration from the old spreadsheet exports. Reads `worship_*.csv`, `_role__*.csv`, `person_*.csv`, `person_role_*.csv`, `schedule_assignment_*.csv`, `kolekte_*.csv` from the given directory. Idempotent. Also populates `pelayanan_categories` from `person_role` data. Pass `--dry-run` to preview.

---

## Settings and environment

Settings split: `base.py` → `dev.py` / `prod.py`. Selected via `DJANGO_SETTINGS_MODULE`.

Key env vars (see `.env.example`):
```
DJANGO_SECRET_KEY=
DJANGO_DEBUG=True/False
DJANGO_ALLOWED_HOSTS=
DATABASE_URL=sqlite:///db.sqlite3          # or postgres://...
NPM_BIN_PATH=npm.cmd                       # Windows default; Linux/nvm: /usr/bin/npm or ~/.nvm/versions/node/vX/bin/npm
DJANGO_SUPERUSER_YOSUA_PASSWORD=           # used by seed_superusers
DJANGO_SUPERUSER_AAMSA_PASSWORD=           # used by seed_superusers
```

`AUTH_USER_MODEL = "accounts.User"` — always reference via `settings.AUTH_USER_MODEL` or `get_user_model()`.

`LOGIN_REDIRECT_URL = "ministry:schedule_list"` — login lands on the schedule list.

---

## Running locally (macOS/Linux)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements/dev.txt
cp .env.example .env          # set DJANGO_SECRET_KEY; set NPM_BIN_PATH to npm location

# Node 20 required for Tailwind build. Install via nvm if not present:
#   curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
#   source ~/.nvm/nvm.sh && nvm install 20 && nvm use 20
# Then set NPM_BIN_PATH=~/.nvm/versions/node/v20.x.x/bin/npm in .env

export NVM_DIR="$HOME/.nvm" && source "$NVM_DIR/nvm.sh"   # if using nvm
python manage.py tailwind install
python manage.py tailwind build
python manage.py migrate

# Seed users and import legacy data (optional):
DJANGO_SUPERUSER_YOSUA_PASSWORD=admin123 python manage.py seed_superusers
python manage.py import_legacy_csv csv/   # if csv/ directory is present

# Two terminals:
python manage.py tailwind start    # terminal 1: Tailwind watcher
python manage.py runserver         # terminal 2: Django dev server
```

---

## Tests and lint

```bash
ruff check .
ruff format --check .
pytest
```

Pre-commit hooks run ruff on every commit (`pre-commit install` once after clone).

---

## HTMX patterns

- `django-htmx` middleware exposes `request.htmx`. Views that serve both full-page and partial responses check this:
  ```python
  if request.htmx:
      return render(request, "ministry/_partial.html", context)
  return render(request, "ministry/full_page.html", context)
  ```
- Assignment flows (picker, assign, clear, add, delete) are HTMX-only endpoints; they return partial HTML fragments.
- The modal/picker for assigning users is rendered via HTMX into `_user_picker.html`.
- Kolekte flows (add, edit, delete) swap `#kolekte-section` in place via HTMX. The section partial is `ministry/_kolekte_section.html`; the edit form partial is `ministry/_kolekte_edit_form.html`.

---

## Internationalization

- Primary language: Bahasa Indonesia (`LANGUAGE_CODE = "id"`).
- Secondary: English.
- Translations live in `locale/`. Always use `gettext_lazy` (`_()`) in models and forms; `gettext` in views.
- After adding/changing strings: `python manage.py makemessages -l id -l en`, then `python manage.py compilemessages`.
- The term "Pelayanan" stays untranslated in the English UI — it is the proper noun for the concept.
- Layouts must hold for strings up to 200% of English length (Indonesian can be longer). Never hard-code widths around translatable text.

---

## Design system (enforced — do not deviate)

Full spec in `DESIGN.md`. Key constraints for code:

**Light only.** No dark mode. If the OS is in dark mode, the app stays light by design.

**Color tokens** (OKLCH, defined in `theme/static_src/src/styles.css` `@theme` block):
- Surfaces: `--color-surface`, `--color-card`, `--color-ink`, `--color-ink-muted`, `--color-divider`
- Brand: `--color-primary`, `--color-primary-dark`, `--color-primary-50`
- Accent (sparingly): `--color-accent`, `--color-accent-50`
- Semantic: `--color-danger`, `--color-success`, `--color-warn` (each with `-50` wash variants)
- Never `#000` or `#fff` — every neutral has chroma toward 290°.

**Typography**: Inter variable, self-hosted. One family only. Scale tokens `--text-2xs` through `--text-3xl`. Headings weight 600, buttons/labels 500, body 400, badges 700.

**Component classes** (in `@layer components`):
- Buttons: `.btn`, `.btn-primary`, `.btn-secondary`, `.btn-ghost`, `.btn-danger`, `.btn-danger-soft`, `.btn-dashed`; sizes `.btn-sm`, `.btn-lg`, `.btn-icon`, `.btn-block`
- Cards: `.card`, `.card-tight`, `.card-roomy`, `.card-interactive`
- Inputs: `.input`, `.select`, `.textarea`, `.input-sm`, `.select-sm`
- Badges: `.badge`, `.badge-primary`, `.badge-success`, `.badge-danger`
- Modal: `.modal-backdrop` + `.modal-panel`
- Toast: `.toast` + variants; Alpine store backed, Django messages bridge
- Utility: `.spinner`, `.skeleton`, `.tab-link`, `.segmented`, `.empty-state`
- Spacing: `.stack-tight` (0.5rem), `.stack-loose` (1.25rem)

**Anti-bans:**
- No nested cards.
- No identical-card grids for >3 entries.
- No hero-metric templates.
- No decorative gradients (solid colors only).
- No em dashes (`—` or `--`) in copy.

**Copy rules:**
- Buttons / headings: Title Case, no trailing period.
- Field labels, helper text: Sentence case, no trailing period.
- Empty-state and error messages: full sentences with terminal punctuation.

**Motion** (only `transform` + `opacity`):
- Custom easings only: `--ease-out-strong`, `--ease-out-soft`, `--ease-in-out-strong`, `--ease-drawer`, `--ease-press`
- Duration tokens: `--dur-instant` (80ms), `--dur-fast` (150ms), `--dur-base` (220ms), `--dur-page` (260ms)
- `prefers-reduced-motion: reduce` kills transforms; preserves opacity/color.

---

## Deployment (summary)

See `DEPLOYMENT.md` for full details.

- Production: Ubuntu 24.04, Gunicorn on `127.0.0.1:8010`, nginx reverse proxy, Cloudflare CDN/proxy.
- Env file: `/etc/poukmaranatha.env` (root:poukmaranatha, mode 640).
- Systemd unit: `poukmaranatha.service`.
- Update: SSH in, `sudo -iu poukmaranatha`, `cd /srv/poukmaranatha`, `./scripts/update.sh`.
- Logs: `journalctl -u poukmaranatha -f`.

---

## URL structure

```
/                           → ministry:schedule_list (login redirect)
/me/                        → ministry:my_schedule
/schedules/new/             → ministry:schedule_create
/schedules/<pk>/            → ministry:schedule_detail
/schedules/<pk>/edit/       → ministry:schedule_edit
/assignments/<pk>/picker/   → HTMX: user picker modal
/assignments/<pk>/assign/   → HTMX POST: assign user
/assignments/<pk>/clear/    → HTMX POST: clear slot
/assignments/<pk>/delete/   → HTMX POST: delete empty slot
/manage/pelayanan/          → admin: Pelayanan list/CRUD
/manage/user-roles/         → admin: UserRole list/CRUD
/manage/users/              → admin: User list
/manage/users/new/          → admin: Create user
/manage/users/<pk>/         → admin: Edit user (includes pelayanan_categories + user_roles checkboxes)
/manage/users/<pk>/delete/  → admin: Delete user
/profile/                   → self: Edit own profile
/schedules/<pk>/kolekte/    → Kolekte list for a schedule (standalone page)
/schedules/<pk>/kolekte/add/→ HTMX POST: add kolekte entry
/kolekte/<pk>/edit/         → HTMX GET/POST: edit kolekte entry
/kolekte/<pk>/delete/       → HTMX POST: delete kolekte entry
/accounts/login/            → Django auth login
/demo/                      → core: HTMX/Tailwind/Alpine demo
```
