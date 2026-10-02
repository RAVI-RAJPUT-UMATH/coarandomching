# Deploying to PythonAnywhere

Step-by-step guide to putting this site online. Takes about 20–30 minutes the
first time. Everything here works on the **free** plan.

Why PythonAnywhere: this app keeps its data in two files on disk —
`database.db` and the `uploads/` folder. PythonAnywhere gives you a real
persistent disk, so both survive restarts. Serverless hosts (Vercel, Netlify)
wipe the disk on every cold start, which is why uploads and edits vanished there.

---

## Before you start

Generate a secret key and keep it somewhere safe — you will paste it in Step 7:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

**Do not commit this key to GitHub.** It is what stops someone forging an admin
login.

---

## Step 1 — Create the account

1. Go to **pythonanywhere.com** → **Pricing & signup** → **Create a Beginner
   account** (free).
2. Pick a username carefully — it becomes your web address:
   `yourusername.pythonanywhere.com`. Something like `jkclasses` reads well.
3. Confirm your email.

## Step 2 — Open a console

Dashboard → **Consoles** → **Bash**.

## Step 3 — Get the code onto the server

```bash
git clone https://github.com/RAVI-RAJPUT-UMATH/coarandomching.git jk
cd jk
ls
```

You should see `app.py`, `db.py`, `templates/`, `static/`.

> `database.db` and `uploads/` are deliberately **not** in Git. Step 8 copies
> your real content across.

## Step 4 — Create a virtual environment

```bash
mkvirtualenv --python=/usr/bin/python3.11 jkenv
pip install -r requirements.txt
```

Note the path it prints — usually `/home/YOURUSERNAME/.virtualenvs/jkenv`.
If Python 3.11 is unavailable, any 3.10+ works.

## Step 5 — Create the web app

1. Go to the **Web** tab → **Add a new web app**.
2. Domain: accept the default → **Next**.
3. Framework: choose **Manual configuration** (⚠️ *not* "Flask" — manual gives
   you control of the WSGI file).
4. Python version: match what you used in Step 4 → **Next**.

## Step 6 — Point it at the app

Still on the **Web** tab:

**Source code**: `/home/YOURUSERNAME/jk`

**Virtualenv**: `/home/YOURUSERNAME/.virtualenvs/jkenv`

**WSGI configuration file**: click the link to open the editor, delete
everything in it, and paste this (replace `YOURUSERNAME`):

```python
import sys

path = "/home/YOURUSERNAME/jk"
if path not in sys.path:
    sys.path.insert(0, path)

from wsgi import application
```

Save it.

**Static files** — add one mapping so CSS and images are served fast:

| URL | Directory |
|---|---|
| `/static/` | `/home/YOURUSERNAME/jk/static` |

> Do **not** add a mapping for `/uploads/`. Those are served by a Flask route
> so the missing-file fallback keeps working.

## Step 7 — Set the secret key

On the **Web** tab, find **Environment variables** and add:

| Name | Value |
|---|---|
| `SECRET_KEY` | the long string you generated above |

Without this the app falls back to a key that is published in the source code,
and `wsgi.py` will print a warning in your error log.

## Step 8 — Upload your existing content

Your results, events and photos live in `database.db` and `uploads/`. Move them
from your laptop:

1. **Files** tab → navigate into `/home/YOURUSERNAME/jk`
2. **Upload a file** → choose `database.db` from your computer
3. Open the `uploads` folder (create it if missing) and upload your photos there

If you skip this, the site still works — it just starts with the sample content
and you add everything through the admin panel.

## Step 9 — Go live

**Web** tab → the big green **Reload** button.

Open `https://yourusername.pythonanywhere.com` — the site should be live, with
HTTPS already working.

## Step 10 — Secure the admin account

1. Go to `/admin/login`, log in with `admin` / `jkclasses123`
2. **Settings → Change Your Password** — change it immediately

The default is written in the README, so anyone who reads the repo knows it.

---

## Keeping it running

**Free plan**: PythonAnywhere asks you to click a "Run until 3 months from
today" button on the Web tab every three months. You get an email reminder. Miss
it and the site goes offline until you click it — nothing is deleted.

**Updating the code** after you change something locally:

```bash
cd ~/jk
git pull
```

then **Reload** on the Web tab.

**Backups** — do this monthly. Download `database.db` and the `uploads/` folder
from the Files tab. That pair is your entire website.

---

## Your own domain name

The free plan only gives `yourusername.pythonanywhere.com`. For
`jkclassesbarnagar.com`:

1. Register the domain (GoDaddy, BigRock, Namecheap) — roughly ₹900–1,200/year
   for `.com`, less for `.in`
2. Upgrade to the **Hacker** plan (about $5/month)
3. Web tab → add your domain, then set the CNAME record PythonAnywhere shows you
   at your registrar

---

## If something goes wrong

**"Something went wrong :-("** — Web tab → **Error log**. The last lines show
the Python traceback. Usually a missing package (`pip install` inside the
virtualenv) or a wrong path in the WSGI file.

**Site loads but has no styling** — the static files mapping in Step 6 is wrong.
Check for a typo in the directory path.

**Photos show "Photo coming soon"** — the files are not in `uploads/`. Re-check
Step 8. This placeholder is deliberate: a missing file degrades gracefully
instead of showing a broken image.

**Uploads fail** — check free-plan disk usage (512 MB) on the Dashboard. The
whole site is roughly 30 MB plus your photos.
