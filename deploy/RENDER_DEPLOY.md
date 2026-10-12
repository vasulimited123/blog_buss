# Deploying Elevate Life to Render (free tier, uses your Neon database)

Render runs the app with **gunicorn**, pulls straight from GitHub, and can
reach your Neon Postgres database (unlike PythonAnywhere's free tier).

---

## One-time setup

### 1. Create a Render account
Go to https://render.com and sign up with your **GitHub** account (easiest —
it lets Render see your repos). No credit card needed for the free tier.

### 2. Create the web service from your repo
1. Render dashboard → **New +** → **Web Service**.
2. Connect/select the repo **`vasulimited123/blog_buss`**.
3. Render may auto-detect `render.yaml`. Either accept the Blueprint, or
   fill the fields manually:
   - **Name:** elevate-life
   - **Region:** Oregon (US) — keep near Neon's US region
   - **Branch:** main
   - **Runtime:** Python
   - **Build Command:** `./build.sh`
   - **Start Command:** `gunicorn config.wsgi:application -c deploy/gunicorn.conf.py`
   - **Instance type:** Free

### 3. Set environment variables
In the service's **Environment** section, add these:

| Key | Value |
|-----|-------|
| `DJANGO_DEBUG` | `false` |
| `DJANGO_SECRET_KEY` | a long random string (or let Render generate) |
| `DATABASE_URL` | `postgresql://neondb_owner:PASSWORD@ep-dry-credit-ae6u7mzc-pooler.c-2.us-east-2.aws.neon.tech/wellness?sslmode=require` |
| `PYTHON_VERSION` | `3.12.6` |

> You do NOT need to set `DJANGO_ALLOWED_HOSTS` — the app automatically trusts
> Render's hostname via `RENDER_EXTERNAL_HOSTNAME`.

### 4. Deploy
Click **Create Web Service**. Render will:
- run `build.sh` (install deps, collectstatic, migrate)
- start gunicorn

Watch the **Logs** tab. When you see gunicorn start and "Live", open the URL
Render gives you (like `https://elevate-life.onrender.com`).

### 5. Create your admin user
In the service → **Shell** tab:
```
python manage.py createsuperuser
```

---

## Verify the live site
- Homepage with Elevate Life logo + 12 articles
- An article page (styled, with editor note)
- `/admin/` login
- `/about/`, `/contact/` (Dr. Agrawal profile)
- `/sitemap.xml`, `/robots.txt`, `/ads.txt`

---

## Notes about the free tier
- The app **sleeps after 15 min idle**; first visit after that takes ~30s to
  wake. Fine for launch/testing.
- For always-on + a custom domain + AdSense, upgrade to the Starter plan
  (~$7/mo) later, add your domain, and set `DJANGO_ALLOWED_HOSTS` +
  `DJANGO_CSRF_TRUSTED_ORIGINS` to the real domain.

## Updating later
Just `git push` to GitHub — Render auto-deploys the new commit.

## Images
Add the 4 PNGs to `static/images/` in the repo
(`dr-agrawal.png`, `gallery-1/2/3.png`), push, and Render redeploys with them.

## Security reminder
Your Neon password is currently in the committed `.env`. On Render the real
value comes from the dashboard env var, so before going public: rotate the
Neon password and remove `.env` from the repo.
