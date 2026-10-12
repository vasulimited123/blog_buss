"""
PythonAnywhere WSGI configuration for Elevate Life.

HOW TO USE ON PYTHONANYWHERE
----------------------------
1. On the PythonAnywhere "Web" tab, click the link to edit your WSGI file
   (it lives at /var/www/<username>_pythonanywhere_com_wsgi.py).
2. DELETE everything in that file.
3. PASTE the contents of THIS file into it.
4. Change `PROJECT_HOME` below to your actual project path, e.g.:
       /home/yourusername/blog_buss
5. Save, then click "Reload" on the Web tab.

NOTE: PythonAnywhere runs Django through this WSGI file (via its own server).
It does NOT use gunicorn. A gunicorn config is included separately only for
other hosts / local production testing.
"""

import os
import sys

# ---------------------------------------------------------------------------
# 1. Point this at your project folder on PythonAnywhere.
#    (The folder that contains manage.py — e.g. where you cloned the repo.)
# ---------------------------------------------------------------------------
PROJECT_HOME = "/home/YOURUSERNAME/blog_buss"

if PROJECT_HOME not in sys.path:
    sys.path.insert(0, PROJECT_HOME)

# ---------------------------------------------------------------------------
# 2. Django settings module.
# ---------------------------------------------------------------------------
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# ---------------------------------------------------------------------------
# 3. Production environment variables.
#
#    The project also reads a committed `.env` file, so if your `.env`
#    already contains DATABASE_URL etc., you may not need to set these here.
#    But setting them here (or in the .env) is what flips the site into
#    production mode. Uncomment and fill in to override:
# ---------------------------------------------------------------------------
# os.environ["DJANGO_DEBUG"] = "false"
# os.environ["DJANGO_SECRET_KEY"] = "replace-with-a-long-random-string"
# os.environ["DJANGO_ALLOWED_HOSTS"] = "yourusername.pythonanywhere.com"
# os.environ["DJANGO_CSRF_TRUSTED_ORIGINS"] = "https://yourusername.pythonanywhere.com"
# os.environ["DATABASE_URL"] = "postgresql://USER:PASSWORD@HOST/wellness?sslmode=require"

# ---------------------------------------------------------------------------
# 4. Serve the Django application.
# ---------------------------------------------------------------------------
from django.core.wsgi import get_wsgi_application  # noqa: E402

application = get_wsgi_application()
