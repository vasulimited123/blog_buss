# Sharing Data via Git & Deploying

You build content locally (PostgreSQL) and need to move it to production.
There are **two ways**, and you can use either or both.

---

## Option A — Re-run the seed command on the server (simplest)

All 26 launch articles live in Python code:
`blog/management/commands/seed_content.py` + `_content_batch1..6.py`.

These files ARE committed to Git. So on the server you simply run:

```
python manage.py migrate
python manage.py seed_content
```

This recreates all posts, categories, authors, tags, and the reviewer.
It is idempotent (safe to run again).

**Use this for:** the initial launch content that we generated.

---

## Option B — Export/import a data fixture (for content you add via the admin)

Once the site is live, you (and writers) will add/edit posts through the
Django admin. That content is NOT in the seed code. To move it between
machines via Git, use Django fixtures.

### Export (on the machine that HAS the data — e.g. your local)

```
python manage.py dumpdata blog --indent 2 --natural-foreign --natural-primary -o blog/fixtures/content.json
```

This writes all blog-app data (posts, categories, tags, authors, reviewers,
subscribers) to a JSON file. **Commit that JSON to Git.**

> Tip: to exclude newsletter subscribers (personal emails) from Git, run:
> ```
> python manage.py dumpdata blog --exclude blog.NewsletterSubscriber --indent 2 --natural-foreign --natural-primary -o blog/fixtures/content.json
> ```

### Import (on the machine that NEEDS the data — e.g. production)

```
python manage.py migrate
python manage.py loaddata content.json
```

Django finds fixtures automatically inside any app's `fixtures/` folder,
so `loaddata content.json` works.

---

## What fixtures DO and DON'T include

Included: posts, categories, tags, authors, medical reviewers, and
(optionally) newsletter subscribers.

NOT included:
- **Your admin superuser / passwords** — create separately on the server
  with `python manage.py createsuperuser`.
- **Uploaded image files** — fixtures store only the file *path*, not the
  file. Upload images on the server, or copy the `media/` folder separately.

---

## Recommended workflow for you

1. **Launch:** commit the seed code (already done) → on server run
   `migrate` then `seed_content`.
2. **Ongoing:** write new posts in the admin locally → `dumpdata` to a
   committed fixture → deploy → `loaddata`.
   (Or just write directly in the production admin once live.)

---

## Deploy checklist (env vars to set in production)

Set these on your host (Railway / Render / etc.), never in Git:

```
DJANGO_SECRET_KEY=<a long random string>
DJANGO_DEBUG=false
DJANGO_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Production database (e.g. Neon free Postgres):
DJANGO_DB_ENGINE=django.db.backends.postgresql
DJANGO_DB_NAME=<db name>
DJANGO_DB_USER=<db user>
DJANGO_DB_PASSWORD=<db password>
DJANGO_DB_HOST=<db host>
DJANGO_DB_PORT=5432
```

Then on the server:
```
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py seed_content        # or loaddata content.json
python manage.py createsuperuser
gunicorn config.wsgi
```
