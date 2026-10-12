"""
Django settings for the wellness blog platform.

Django-only project (server-rendered templates, no React/Next.js).
Development uses SQLite; production will switch to PostgreSQL.
"""

import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Lightweight .env loader (no external dependency).
# Reads KEY=VALUE lines from a `.env` file at the project root and injects
# them into os.environ (without overriding vars already set in the real
# environment). The .env file is git-ignored, so secrets never reach Git.
# ---------------------------------------------------------------------------
def load_dotenv(path):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            for raw in fh:
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                os.environ.setdefault(key, value)
    except FileNotFoundError:
        pass


load_dotenv(BASE_DIR / ".env")


def env_bool(name, default):
    """Read a boolean from the environment ('1', 'true', 'yes' => True)."""
    val = os.environ.get(name)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "on")


# ---------------------------------------------------------------------------
# Core security / debug
#
# In production, set these environment variables:
#   DJANGO_SECRET_KEY   — a long random string
#   DJANGO_DEBUG        — "false"
#   DJANGO_ALLOWED_HOSTS — comma-separated, e.g. "example.com,www.example.com"
# ---------------------------------------------------------------------------
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "dev-only-insecure-key-change-before-deploy",  # dev fallback only
)

DEBUG = env_bool("DJANGO_DEBUG", True)

_hosts = os.environ.get("DJANGO_ALLOWED_HOSTS", "")
ALLOWED_HOSTS = (
    [h.strip() for h in _hosts.split(",") if h.strip()]
    if _hosts
    else ["localhost", "127.0.0.1", "[::1]"]
)

# Render provides the external hostname automatically — trust it so the site
# works on first deploy without having to know the URL in advance.
_render_host = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
if _render_host:
    ALLOWED_HOSTS.append(_render_host)

# When you serve over HTTPS behind a proxy/CDN, set DJANGO_CSRF_TRUSTED_ORIGINS
# e.g. "https://example.com,https://www.example.com"
_csrf = os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "")
CSRF_TRUSTED_ORIGINS = [o.strip() for o in _csrf.split(",") if o.strip()] if _csrf else []
if _render_host:
    CSRF_TRUSTED_ORIGINS.append(f"https://{_render_host}")


# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",

    # Third-party
    "django_ckeditor_5",

    # Local apps
    "blog",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # WhiteNoise serves static files efficiently in production.
    # Harmless in development. Requires the `whitenoise` package.
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "blog.context_processors.popular_posts",
                "blog.context_processors.adsense",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# ---------------------------------------------------------------------------
# Database
#
# Development: SQLite (default, zero config).
# Production: set the PostgreSQL env vars below and install psycopg.
#   DJANGO_DB_ENGINE=django.db.backends.postgresql
#   DJANGO_DB_NAME, DJANGO_DB_USER, DJANGO_DB_PASSWORD, DJANGO_DB_HOST, DJANGO_DB_PORT
# ---------------------------------------------------------------------------
def _database_from_url(url):
    """Parse a PostgreSQL connection URL (e.g. a Neon URL) into Django config.

    Handles the ?sslmode=require&channel_binding=require query that Neon adds.
    """
    from urllib.parse import urlparse, parse_qs

    parsed = urlparse(url)
    query = parse_qs(parsed.query)

    options = {}
    sslmode = query.get("sslmode", ["require"])[0]
    if sslmode:
        options["sslmode"] = sslmode
    # NOTE: we deliberately ignore `channel_binding` from the URL. Neon's
    # pooled endpoint can drop the connection when channel_binding=require is
    # passed through psycopg. sslmode=require already secures the connection.

    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": (parsed.path or "/").lstrip("/"),
        "USER": parsed.username or "",
        "PASSWORD": parsed.password or "",
        "HOST": parsed.hostname or "localhost",
        "PORT": str(parsed.port or "5432"),
        "CONN_MAX_AGE": 600,
        "OPTIONS": options,
    }


# Priority: DATABASE_URL (Neon / production) > individual DJANGO_DB_* vars > SQLite.
if os.environ.get("DATABASE_URL"):
    DATABASES = {"default": _database_from_url(os.environ["DATABASE_URL"])}
elif os.environ.get("DJANGO_DB_ENGINE"):
    DATABASES = {
        "default": {
            "ENGINE": os.environ["DJANGO_DB_ENGINE"],
            "NAME": os.environ.get("DJANGO_DB_NAME", ""),
            "USER": os.environ.get("DJANGO_DB_USER", ""),
            "PASSWORD": os.environ.get("DJANGO_DB_PASSWORD", ""),
            "HOST": os.environ.get("DJANGO_DB_HOST", "localhost"),
            "PORT": os.environ.get("DJANGO_DB_PORT", "5432"),
            "CONN_MAX_AGE": 600,
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


# ---------------------------------------------------------------------------
# Password validation
# ---------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# ---------------------------------------------------------------------------
# Internationalization
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True


# ---------------------------------------------------------------------------
# Static & media files
# ---------------------------------------------------------------------------
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# WhiteNoise: compress + cache-bust static files in production.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}


# ---------------------------------------------------------------------------
# Default primary key field type
# ---------------------------------------------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ---------------------------------------------------------------------------
# CKEditor 5 (rich text editor used in the admin for writing articles)
# ---------------------------------------------------------------------------
# Where images uploaded from inside the editor are stored (under MEDIA_ROOT).
CKEDITOR_5_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"
CKEDITOR_5_UPLOAD_FILE_TYPES = ["jpeg", "jpg", "png", "gif", "webp"]

CKEDITOR_5_CONFIGS = {
    "default": {
        "toolbar": [
            "heading", "|",
            "bold", "italic", "link", "bulletedList", "numberedList", "|",
            "blockQuote", "imageUpload", "insertTable", "|",
            "undo", "redo",
        ],
    },
    # A richer profile for writing full articles.
    "article": {
        "toolbar": [
            "heading", "|",
            "bold", "italic", "underline", "link", "|",
            "bulletedList", "numberedList", "blockQuote", "|",
            "imageUpload", "insertTable", "mediaEmbed", "|",
            "sourceEditing", "undo", "redo",
        ],
        "height": 500,
        "width": "100%",
        "image": {
            "toolbar": [
                "imageTextAlternative", "|",
                "imageStyle:alignLeft", "imageStyle:alignCenter", "imageStyle:alignRight",
            ],
        },
        "table": {
            "contentToolbar": ["tableColumn", "tableRow", "mergeTableCells"],
        },
    },
}


# ---------------------------------------------------------------------------
# Google AdSense
#
# Everything is OFF until you set DJANGO_ADSENSE_CLIENT_ID. That keeps the
# site clean (gray placeholders) during development and while awaiting
# approval. After approval, set these env vars in production:
#
#   DJANGO_ADSENSE_CLIENT_ID   e.g. "ca-pub-1234567890123456"
#   DJANGO_ADSENSE_SLOT_TOP        (ad unit id for the top-of-article slot)
#   DJANGO_ADSENSE_SLOT_INARTICLE  (ad unit id for the in-article slot)
#   DJANGO_ADSENSE_SLOT_SIDEBAR    (ad unit id for the sidebar slot)
#
# The slot IDs are the numeric "data-ad-slot" values AdSense gives you when
# you create each ad unit. They are optional — auto ads work with just the
# client id — but named units give you more control.
# ---------------------------------------------------------------------------
ADSENSE_CLIENT_ID = os.environ.get("DJANGO_ADSENSE_CLIENT_ID", "")
ADSENSE_SLOTS = {
    "top": os.environ.get("DJANGO_ADSENSE_SLOT_TOP", ""),
    "in-article": os.environ.get("DJANGO_ADSENSE_SLOT_INARTICLE", ""),
    "sidebar": os.environ.get("DJANGO_ADSENSE_SLOT_SIDEBAR", ""),
}


# ---------------------------------------------------------------------------
# Production security hardening
#
# These settings activate automatically when DEBUG is False (i.e. in
# production). They assume the site is served over HTTPS. If your host
# terminates TLS at a proxy/CDN, the X-Forwarded-Proto header handling below
# lets Django know the original request was secure.
# ---------------------------------------------------------------------------
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", True)

    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

    # HSTS: tell browsers to only use HTTPS. Start modest, raise once confident.
    SECURE_HSTS_SECONDS = int(os.environ.get("DJANGO_HSTS_SECONDS", "3600"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
    X_FRAME_OPTIONS = "DENY"
