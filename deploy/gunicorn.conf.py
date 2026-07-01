"""Gunicorn configuration for poukmaranatha (production).

Used by the systemd unit:
    ExecStart=.../.venv/bin/gunicorn --config deploy/gunicorn.conf.py config.wsgi:application
"""

# Bind on the loopback only — nginx fronts us
bind = "127.0.0.1:8010"

# 3 sync workers is enough for a church-roster app with ~50 users.
# Scale up by editing this file (and reloading the service) if traffic grows.
workers = 3
worker_class = "sync"
threads = 1

# Restart workers occasionally to keep memory predictable.
max_requests = 1000
max_requests_jitter = 100

# Long enough for slow Postgres queries on first boot, short enough to fail fast.
timeout = 60
graceful_timeout = 30
keepalive = 5

# Tell systemd we're alive so Type=notify works.
# (gunicorn 20.1+ supports systemd notify natively.)

# Logs go to stdout/stderr → captured by journald via the systemd unit.
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(L)ss'

# Reload on SIGHUP
preload_app = False
