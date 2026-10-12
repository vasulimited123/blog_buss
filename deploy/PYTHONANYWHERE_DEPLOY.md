# Deploying Elevate Life to PythonAnywhere

A complete, step-by-step guide. Follow it top to bottom.

> PythonAnywhere runs Django through **its own WSGI server** (not gunicorn).
> Gunicorn files are included only for other hosts.

---

## Before you start

- You have a PythonAnywhere account (free tier works for testing; the
  **Hacker plan ($5/mo)** is required for a custom domain + AdSense).
- Your code is on GitHub: `https://github.com/vasulimited123/blog_buss`
- Your Neon database already has the content (done).

---

## Step 1 — Open a Bash console on PythonAnywhere

On the PythonAnywhere dashboard: **Consoles → Bash**.

---

## Step 2 — Clone your repository

```bash
git clone https://github.com/vasulimited123/blog_buss.git
cd blog_buss
```

---

## Step 3 — Create a virtual environment and install dependencies

PythonAnywhere has several Python versions. Use 3.11 or 3.12 (stable there).

```bash
python3.11 --version        # confirm it exists
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

> If `psycopg[binary]` has trouble installing, run:
> `pip install "psycopg[binary]"` on its own, or use `psycopg2-binary`.

---

## Step 4 — Confirm environment variables

Your repo includes a committed `.env`, so `DATABASE_URL` is already set.
For production you should ALSO ensure these are set (edit the `.env` on the
server, OR set them in the WSGI file in Step 7):

```
DJANGO_DEBUG=false
DJANGO_SECRET_KEY=<a long random string>
DJANGO_ALLOWED_HOSTS=YOURUSERNAME.pythonanywhere.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://YOURUSERNAME.pythonanywhere.com
DATABASE_URL=postgresql://neondb_owner:...@...neon.tech/wellness?sslmode=require
```

To generate a strong secret key:
```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

Edit the `.env`:
```bash
nano .env        # update DJANGO_DEBUG=false, add SECRET_KEY + ALLOWED_HOSTS
```

---

## Step 5 — Run migrations and collect static files

```bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser     # create your admin login on the server
```

(Migrations will say "no migrations to apply" if Neon is already migrated —
that's fine. The data is already there.)

---

## Step 6 — Create the Web app on PythonAnywhere

1. Go to the **Web** tab → **Add a new web app**.
2. Choose **Manual configuration** (NOT the Django quickstart).
3. Choose the **same Python version** you used for the venv (3.11).

---

## Step 7 — Configure the Web app

On the **Web** tab, set these fields:

**Virtualenv:**
```
/home/YOURUSERNAME/blog_buss/venv
```

**Source code:**
```
/home/YOURUSERNAME/blog_buss
```

**WSGI configuration file** (click to edit it):
- Delete everything in it.
- Paste the contents of `deploy/pythonanywhere_wsgi.py` from this repo.
- Change `PROJECT_HOME` to `/home/YOURUSERNAME/blog_buss`.
- Save.

---

## Step 8 — Static files mapping

On the **Web** tab, under **Static files**, add a mapping:

| URL        | Directory                                        |
|------------|--------------------------------------------------|
| `/static/` | `/home/YOURUSERNAME/blog_buss/staticfiles`       |
| `/media/`  | `/home/YOURUSERNAME/blog_buss/media`             |

(These serve the CSS/JS/images and any uploaded media.)

---

## Step 9 — Reload and test

Click the big **Reload** button on the Web tab, then visit:

```
https://YOURUSERNAME.pythonanywhere.com
```

Check:
- Homepage loads with the Elevate Life logo and articles
- An article page renders with styling
- `/admin/` login works
- `/about/`, `/contact/` (Dr. Agrawal profile), legal pages load
- `/sitemap.xml`, `/robots.txt`, `/ads.txt` respond

---

## Step 10 — Add your images

Put the 4 PNGs in `static/images/` in the repo:
`dr-agrawal.png`, `gallery-1.png`, `gallery-2.png`, `gallery-3.png`.
Then on the server:
```bash
cd ~/blog_buss && git pull
python manage.py collectstatic --noinput
```
Reload the web app.

---

## Updating the site later (your deploy routine)

Whenever you push changes to GitHub:
```bash
cd ~/blog_buss
git pull
source venv/bin/activate
pip install -r requirements.txt        # only if dependencies changed
python manage.py migrate               # only if models changed
python manage.py collectstatic --noinput
# then click "Reload" on the Web tab
```

---

## Going live with a custom domain + AdSense (later)

1. Upgrade to the **Hacker plan** ($5/mo) — required for custom domains.
2. Buy your domain (e.g. elevatelife.in).
3. On the Web tab, set your domain and add the CNAME record PythonAnywhere
   gives you at your domain registrar.
4. Enable HTTPS (free, provided by PythonAnywhere).
5. Update `DJANGO_ALLOWED_HOSTS` and `DJANGO_CSRF_TRUSTED_ORIGINS` to the
   real domain, and reload.
6. Apply to AdSense with the real domain. After approval set
   `DJANGO_ADSENSE_CLIENT_ID` → ads + ads.txt activate automatically.

---

## Troubleshooting

- **Error / 502:** Check the **Error log** link on the Web tab — it shows the
  exact Python traceback.
- **CSS missing / unstyled site:** You forgot `collectstatic`, or the static
  files mapping path is wrong.
- **DisallowedHost error:** Add your PythonAnywhere domain to
  `DJANGO_ALLOWED_HOSTS`.
- **DB connection error:** Check `DATABASE_URL`. Note Neon may be slow from
  some regions; keep the Neon region close to the PythonAnywhere region (US).
- **Database password:** remember your `.env` with the Neon password is in the
  public repo. Rotate it in Neon and remove `.env` from the repo before going
  fully public.
```
