# Deployment

This document covers two flows:

1. [Fresh install](#1-fresh-install-on-a-new-ubuntu-vm) — bring a brand-new Ubuntu 24 server from zero to a live `poukmaranatha.ionyx.org`.
2. [Update flow](#2-update-flow-local--git--vm) — push a code change locally and refresh the droplet.

The reference deployment lives on a multi-app DigitalOcean droplet (alongside ionyx, pocket, sablonmechanics, n8n) but every step here is generic Ubuntu 24.04 + Postgres 16 + nginx.

**Convention used throughout:**

| | |
|---|---|
| Linux user | `poukmaranatha` |
| App path | `/srv/poukmaranatha` |
| Gunicorn port | `127.0.0.1:8010` |
| Postgres role / db | `poukmaranatha` / `poukmaranatha` |
| Env file | `/etc/poukmaranatha.env` |
| Systemd unit | `poukmaranatha.service` |
| Nginx site | `/etc/nginx/sites-available/poukmaranatha` |
| Public hostname | `poukmaranatha.ionyx.org` (Cloudflare proxied) |

Pick a different name for these if your hostname differs — but stay consistent.

---

## 1. Fresh install on a new Ubuntu VM

Prerequisites:
- Ubuntu 24.04 (or close).
- Root SSH access.
- A DNS A record pointing your domain at the droplet (Cloudflare proxied is fine).
- Postgres 16 already running on the box (or install via `apt install postgresql`).
- nginx already running on the box (or install via `apt install nginx`).
- Node 20+ already on the box (or install via `apt install nodejs npm`).

Every step below assumes you're SSH'd in as **root** (or with `sudo` rights) unless otherwise noted.

### 1.1  Install OS dependencies

```bash
apt-get update
apt-get install -y \
    python3.12 python3.12-venv python3.12-dev \
    libpq-dev build-essential gettext \
    nginx certbot python3-certbot-nginx \
    postgresql-16
```

Idempotent — already-installed packages are skipped.

> **What this gives you:** Python 3.12 with venv support, the C headers needed by `psycopg`, gettext for translation `.mo` compilation, nginx + certbot for HTTPS, and Postgres 16. Skip what's already installed.

### 1.2  Create the Linux user

```bash
useradd -m -s /bin/bash poukmaranatha
usermod -aG www-data poukmaranatha
```

> **Why:** every app on the droplet runs as its own Linux user so a compromise in one app can't reach another's files. Adding to `www-data` lets nginx read static files later.

### 1.3  Create the Postgres role and database

```bash
sudo -u postgres createuser poukmaranatha --pwprompt
sudo -u postgres createdb -O poukmaranatha poukmaranatha
```

The first command prompts for a password. **Save it now** — you'll paste it into the env file in step 1.6.

Optional, but recommended (matches the convention used by other apps on the droplet):

```bash
sudo -u root tee /root/.poukmaranatha-db-pw <<'PW'
<paste-the-password-here>
PW
chmod 600 /root/.poukmaranatha-db-pw
```

> **Why:** keeps a recovery copy of the password root-readable only, in case `/etc/poukmaranatha.env` ever gets clobbered.

### 1.4  Clone the repo

```bash
sudo -u poukmaranatha git clone https://github.com/aamsa/poukmaranatha.git /srv/poukmaranatha
```

If you use a private fork, add a deploy key first.

### 1.5  Python virtualenv + dependencies

```bash
cd /srv/poukmaranatha
sudo -u poukmaranatha python3.12 -m venv .venv
sudo -u poukmaranatha .venv/bin/pip install --upgrade pip
sudo -u poukmaranatha .venv/bin/pip install -r requirements/prod.txt
```

Verify the install:

```bash
sudo -u poukmaranatha .venv/bin/python -c "import django, gunicorn, psycopg; print(django.VERSION, gunicorn.__version__)"
```

### 1.6  Build the static assets (Tailwind + vendor JS + Inter font)

```bash
cd /srv/poukmaranatha/theme/static_src
sudo -u poukmaranatha npm install
sudo -u poukmaranatha npm run build
```

This compiles Tailwind, copies htmx + alpine into `theme/static/vendor/`, and downloads the Inter variable font on first run.

### 1.7  Write the env file

Generate a fresh secret key:

```bash
SECRET_KEY=$(.venv/bin/python -c "import secrets; print(secrets.token_urlsafe(64))")
echo "$SECRET_KEY"   # save it somewhere safe
```

Get the Postgres password from step 1.3:

```bash
DB_PW=$(cat /root/.poukmaranatha-db-pw)
```

Write `/etc/poukmaranatha.env` (root:poukmaranatha, mode 640):

```bash
cat >/etc/poukmaranatha.env <<EOF
DJANGO_SETTINGS_MODULE=config.settings.prod
DJANGO_SECRET_KEY=$SECRET_KEY
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=poukmaranatha.ionyx.org
DATABASE_URL=postgres://poukmaranatha:$DB_PW@127.0.0.1:5432/poukmaranatha
NPM_BIN_PATH=/usr/bin/npm
DJANGO_SUPERUSER_AAMSA_PASSWORD=poer123
DJANGO_SUPERUSER_YOSUA_PASSWORD=theking0wfar
EOF
chown root:poukmaranatha /etc/poukmaranatha.env
chmod 640 /etc/poukmaranatha.env
```

> **Security note:** the file is readable only by root and the `poukmaranatha` group. The systemd unit reads it with `EnvironmentFile=` at service start.

### 1.8  Run Django bootstrap commands

Become the app user, load the env, run the four commands, exit:

```bash
sudo -iu poukmaranatha
cd /srv/poukmaranatha
set -a; . /etc/poukmaranatha.env; set +a
.venv/bin/python manage.py migrate
.venv/bin/python manage.py collectstatic --noinput
.venv/bin/python manage.py compilemessages
.venv/bin/python manage.py seed_superusers
exit
```

Expected output from the last command:

```
created superuser 'aamsa' (account_role=superuser)
created superuser 'yosua' (account_role=superuser)
```

> **What each step does:**
> - `migrate` — creates the database schema.
> - `collectstatic` — gathers all static files into `staticfiles/` (where nginx will serve them from). Manifest-hashed via WhiteNoise's `CompressedManifestStaticFilesStorage`.
> - `compilemessages` — turns the `.po` translation files into `.mo` (binary) format that Django actually loads.
> - `seed_superusers` — creates `aamsa` and `yosua` with the passwords from the env file. Idempotent — safe to re-run.

### 1.9  Install the systemd unit

```bash
cp /srv/poukmaranatha/deploy/poukmaranatha.service /etc/systemd/system/poukmaranatha.service
systemctl daemon-reload
systemctl enable --now poukmaranatha
systemctl status poukmaranatha
```

You should see `active (running)`. If not, see [Troubleshooting](#troubleshooting).

Local smoke test:

```bash
curl -sI http://127.0.0.1:8010/accounts/login/ | head -1
# HTTP/1.1 200 OK
```

### 1.10  Allow the deploy user to restart the service

The update script (used in the [Update flow](#2-update-flow-local--git--vm)) calls `sudo systemctl restart poukmaranatha`. Add a sudoers drop-in so this doesn't prompt for a password:

```bash
cat >/etc/sudoers.d/poukmaranatha-deploy <<'EOF'
poukmaranatha ALL=(root) NOPASSWD: /bin/systemctl restart poukmaranatha
EOF
chmod 440 /etc/sudoers.d/poukmaranatha-deploy
visudo -c   # validate — should print "/etc/sudoers.d/poukmaranatha-deploy: parsed OK"
```

### 1.11  Install the nginx site (HTTP first)

```bash
cp /srv/poukmaranatha/deploy/nginx-poukmaranatha.conf /etc/nginx/sites-available/poukmaranatha
ln -sf /etc/nginx/sites-available/poukmaranatha /etc/nginx/sites-enabled/poukmaranatha
nginx -t
systemctl reload nginx
```

Smoke test:

```bash
curl -sI -H 'Host: poukmaranatha.ionyx.org' http://127.0.0.1/accounts/login/ | head -1
# HTTP/1.1 200 OK
```

### 1.12  Issue the Let's Encrypt cert

certbot needs HTTP-01 to reach the origin directly, which won't work through Cloudflare's proxy. So:

1. **In the Cloudflare dashboard**, find the `poukmaranatha` A record and click the orange-cloud icon to switch it to **DNS only** (grey cloud). Save.
2. Wait ~30 seconds for DNS propagation.
3. On the droplet:

   ```bash
   certbot --nginx -d poukmaranatha.ionyx.org \
       -m you@example.com --agree-tos --non-interactive --redirect
   ```

   certbot will:
   - prove ownership of the domain (HTTP-01 challenge).
   - install the cert at `/etc/letsencrypt/live/poukmaranatha.ionyx.org/`.
   - rewrite `/etc/nginx/sites-available/poukmaranatha` to add a `listen 443 ssl` block.
   - add an HTTP→HTTPS redirect.
   - reload nginx.

4. Verify:

   ```bash
   certbot certificates                # lists the cert + expiry
   certbot renew --dry-run             # confirms auto-renewal works
   ```

5. **Back in Cloudflare**, click the cloud icon again to switch back to **Proxied** (orange cloud). Save.
6. **In Cloudflare → SSL/TLS → Overview**, set the encryption mode to **Full (strict)**. This makes Cloudflare validate the LE cert at origin, end-to-end TLS.

### 1.13  Verify production is live

```bash
curl -sI https://poukmaranatha.ionyx.org/accounts/login/ | head -3
# HTTP/2 200
# server: cloudflare
```

Then in a browser:
- Visit https://poukmaranatha.ionyx.org/ → redirects to login.
- Log in as `aamsa` (password `poer123`) → reaches the schedule list.
- Log in as `yosua` (password `theking0wfar`) → reaches the schedule list.
- Open any schedule, click **Tugaskan** on a slot → modal opens cleanly (mobile + desktop).

🎉 **Live.**

---

## 2. Update flow (local → git → vm)

Workflow:

```
┌─ local dev ─┐         ┌─ github ─┐          ┌─ droplet ────────────┐
│  edit code  │ git push│   main   │ git pull │ ./scripts/update.sh  │
│  test        │ ───→  │   branch │ ───────→ │ rebuilds + restarts  │
└──────────────┘        └──────────┘          └──────────────────────┘
```

### 2.1  Develop locally

Standard Django dev:

```powershell
.\.venv\Scripts\Activate.ps1
python manage.py runserver
```

In another terminal, watch Tailwind:

```powershell
cd theme\static_src
npm run dev
```

When you're happy:

```bash
git add .
git commit -m "describe what changed"
git push
```

### 2.2  Deploy to the droplet

SSH in and run the update script:

```bash
ssh mydroplet                      # or your alias
sudo -iu poukmaranatha             # become the app user (interactive shell)
cd /srv/poukmaranatha
./scripts/update.sh
```

Expected output:

```
==> 1/7  git pull
✓ updated abc1234 → def5678
==> 2/7  pip install
✓ python deps in sync
==> 3/7  npm install + build
✓ static assets built
==> 4/7  migrate
✓ db schema in sync
==> 5/7  collectstatic
✓ static collected
==> 6/7  compilemessages
✓ translations compiled
==> 7/7  systemctl restart
✓ service active

✓ deploy complete  (def5678)
```

Total time: usually under 30 seconds.

### 2.3  When `update.sh` fails

`update.sh` aborts on the first error (`set -euo pipefail`). The previous version of the service is still running because we only call `systemctl restart` at the end. So:

1. Read the error message.
2. Fix the cause (most often: a new `requirements/prod.txt` entry that needs a system C lib, or a migration that requires manual intervention).
3. Re-run `./scripts/update.sh`. It's idempotent.

### 2.4  Manual deploy (when `update.sh` won't run)

Same commands one by one, as the `poukmaranatha` user inside `/srv/poukmaranatha`:

```bash
git fetch origin && git pull --ff-only
.venv/bin/pip install -r requirements/prod.txt
( cd theme/static_src && npm install && npm run build )
.venv/bin/python manage.py migrate
.venv/bin/python manage.py collectstatic --noinput
.venv/bin/python manage.py compilemessages
sudo systemctl restart poukmaranatha
```

### 2.5  Rolling back

If a deploy goes wrong:

```bash
cd /srv/poukmaranatha
git log --oneline -5            # find the last good commit
git reset --hard <good-commit>
./scripts/update.sh
```

If a migration was applied that you can't undo, that's a real Django problem — fix forward by writing a new migration that reverts it. Don't manually edit migration files on the droplet.

### 2.6  Watching logs

Live tail of gunicorn:

```bash
journalctl -u poukmaranatha -f
```

Last 100 lines (e.g. after a crash):

```bash
journalctl -u poukmaranatha -n 100 --no-pager
```

Nginx access / error:

```bash
tail -f /var/log/nginx/poukmaranatha-access.log
tail -f /var/log/nginx/poukmaranatha-error.log
```

### 2.7  When to skip parts of the update

99% of deploys want every step. But:

- No new dependencies → step 2 (`pip install`) is a no-op (~1 s).
- No template/CSS changes → step 3 (`npm run build`) is still cheap (~5 s); leave it on.
- No migrations → step 4 (`migrate`) is a no-op (~1 s).
- No new translation strings → step 6 (`compilemessages`) is fast (~1 s).

In practice, **always run `./scripts/update.sh`**. The cost of running every step is < 30 s; the cost of skipping a step you needed is a 500 page.

---

## Troubleshooting

### "I get a 502 Bad Gateway"

nginx is up but gunicorn isn't responding on `127.0.0.1:8010`. Check:

```bash
systemctl status poukmaranatha
journalctl -u poukmaranatha -n 50 --no-pager
```

Most common causes:
- Missing or wrong env var → look for `KeyError`, `ImproperlyConfigured`.
- Postgres unreachable → look for `could not connect to server`. Verify `DATABASE_URL` and that postgres is running (`systemctl status postgresql@16-main`).
- Migration failure → look for `django.db.utils.ProgrammingError`.

### "I get a 500 Server Error after a deploy"

Almost always: `collectstatic` wasn't run (or failed silently), so a manifest-hashed asset 404s. Re-run:

```bash
cd /srv/poukmaranatha
.venv/bin/python manage.py collectstatic --noinput
sudo systemctl restart poukmaranatha
```

### "certbot fails the HTTP-01 challenge"

You forgot to switch Cloudflare to "DNS only" (grey cloud) before running certbot. Switch it, wait ~30 s, retry. Switch back to "Proxied" after success.

### "I changed `.po` translations but the site still shows old strings"

`compilemessages` didn't run — the `.mo` binaries are what Django reads at runtime. The update script does this for you; if you ran a manual deploy, run it manually:

```bash
.venv/bin/python manage.py compilemessages
sudo systemctl restart poukmaranatha
```

### "I broke another app on the same droplet"

You shouldn't have — every config in this doc is namespaced to `poukmaranatha`. But if you did:

- Wrong nginx config → `nginx -t` would have caught it. If you bypassed that, restore the old config from `/etc/nginx/sites-available/<other-app>` and reload.
- Wrong Postgres role → only the `poukmaranatha` role and database were created. Other roles weren't touched. If you're unsure, `\du` and `\l` in `psql -U postgres`.
- Wrong port → you used `8010`. If anything else is on it, see `ss -tlnp | grep :8010` and pick a different unused port (8011, 8012…).
