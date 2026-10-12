"""
Gunicorn configuration for Elevate Life.

Used for hosts that run gunicorn (Railway, Render, a VPS, Docker) and for
local production-style testing on Linux/Mac. PythonAnywhere does NOT use
this — it has its own WSGI server (see pythonanywhere_wsgi.py).

Run with:
    gunicorn config.wsgi:application -c deploy/gunicorn.conf.py
"""

import multiprocessing
import os

# Bind to the port the host provides (common on PaaS), default 8000.
bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"

# A sensible default worker count. Override with WEB_CONCURRENCY if needed.
workers = int(os.environ.get("WEB_CONCURRENCY", multiprocessing.cpu_count() * 2 + 1))

# Threads per worker — helps with I/O-bound Django views.
threads = int(os.environ.get("GUNICORN_THREADS", "2"))

# Recycle workers periodically to avoid memory leaks.
max_requests = 1000
max_requests_jitter = 100

timeout = 60
keepalive = 5

accesslog = "-"   # log to stdout
errorlog = "-"
loglevel = os.environ.get("GUNICORN_LOG_LEVEL", "info")
