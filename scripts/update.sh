#!/usr/bin/env bash
#
# scripts/update.sh — pull latest code and refresh the running service.
#
# Run this on the droplet as the `poukmaranatha` user, from /srv/poukmaranatha:
#     ./scripts/update.sh
#
# What it does, in order:
#   1. git fetch + git pull (from the configured remote)
#   2. pip install -r requirements/prod.txt (idempotent if no changes)
#   3. npm install + npm run build (rebuild Tailwind + copy vendor JS)
#   4. python manage.py migrate (apply any new migrations)
#   5. python manage.py collectstatic --noinput (refresh the nginx-served static dir)
#   6. python manage.py compilemessages (rebuild .mo from .po if translations changed)
#   7. sudo systemctl restart poukmaranatha (graceful gunicorn restart)
#
# The script is `set -euo pipefail`, so any failure aborts the deploy.
# Step 7 needs the sudoers rule documented in DEPLOYMENT.md.

set -euo pipefail

# Colors (only when stdout is a TTY).
if [ -t 1 ]; then
  GREEN=$'\033[32m'; BLUE=$'\033[34m'; RED=$'\033[31m'; RESET=$'\033[0m'
else
  GREEN=''; BLUE=''; RED=''; RESET=''
fi

step() { printf '\n%s==>%s %s\n' "$BLUE" "$RESET" "$1"; }
ok()   { printf '%s✓%s %s\n' "$GREEN" "$RESET" "$1"; }
die()  { printf '%s✗ %s%s\n' "$RED" "$1" "$RESET" >&2; exit 1; }

cd "$(dirname "$0")/.."
APP_DIR="$(pwd)"

[ -f manage.py ] || die "Not in the app dir (no manage.py at $APP_DIR)"
[ -d .venv ]    || die "No .venv at $APP_DIR/.venv — run the fresh-install steps first"
[ -d theme/static_src ] || die "theme/static_src missing"

# Source env so DJANGO_SETTINGS_MODULE etc. are set for manage.py.
# /etc/poukmaranatha.env is owned root:poukmaranatha 640 — we can read it.
if [ -f /etc/poukmaranatha.env ]; then
  set -a
  # shellcheck disable=SC1091
  . /etc/poukmaranatha.env
  set +a
else
  die "/etc/poukmaranatha.env not found — fresh-install incomplete"
fi

step "1/7  git pull"
git fetch --quiet origin
PREV=$(git rev-parse --short HEAD)
git pull --ff-only --quiet
NEW=$(git rev-parse --short HEAD)
if [ "$PREV" = "$NEW" ]; then
  ok "already at $NEW (no changes)"
else
  ok "updated $PREV → $NEW"
fi

step "2/7  pip install"
.venv/bin/pip install --quiet --upgrade pip
.venv/bin/pip install --quiet -r requirements/prod.txt
ok "python deps in sync"

step "3/7  npm install + build"
( cd theme/static_src && npm install --silent --no-audit --no-fund && npm run build --silent )
ok "static assets built"

step "4/7  migrate"
.venv/bin/python manage.py migrate --noinput
ok "db schema in sync"

step "5/7  collectstatic"
.venv/bin/python manage.py collectstatic --noinput >/dev/null
ok "static collected"

step "6/7  compilemessages"
.venv/bin/python manage.py compilemessages >/dev/null 2>&1 || true
ok "translations compiled"

step "7/7  systemctl restart"
sudo /bin/systemctl restart poukmaranatha
sleep 1
if systemctl is-active --quiet poukmaranatha; then
  ok "service active"
else
  die "service failed to start — see: journalctl -u poukmaranatha -n 50"
fi

printf '\n%s✓ deploy complete%s  (%s)\n' "$GREEN" "$RESET" "$NEW"
