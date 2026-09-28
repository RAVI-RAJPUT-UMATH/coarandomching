# JK Classes Barnagar — Website & Admin Panel

A complete, responsive website for JK Classes Barnagar with a simple admin panel,
so the whole site can be managed without touching any code.

**Built with:** Python Flask + SQLite + plain HTML/CSS/JavaScript.
No React, no build step, no Docker. Two dependencies in total.

| Document | For |
|---|---|
| **README.md** (this file) | Running the site and using the admin panel |
| [EXPLANATION.md](EXPLANATION.md) | How the code works, explained piece by piece |
| [CLAUDE.md](CLAUDE.md) | Conventions for AI coding assistants |

---

# Part 1 — For the coaching owner

## Starting the website

1. Open the project folder.
2. Double-click **`start.bat`**. A black window opens and your browser launches.
3. The website is at **http://127.0.0.1:5000**

**Keep the black window open** while using the site. Closing it stops the website.

## Logging in

Go to **http://127.0.0.1:5000/admin/login**

| | |
|---|---|
| Username | `admin` |
| Password | `jkclasses123` |

> ⚠️ **Change this password now.** It is written in this file, so anyone who
> reads it knows your password. Go to **Settings → Change Your Password**.

## What you can change

Everything. Pick a section from the blue menu on the left:

| Menu item | Controls |
|---|---|
| **Dashboard** | Overview and shortcuts |
| **Homepage** | Main banner, About text, the four highlight boxes, the numbers strip |
| **Results** | Student names, percentages, photos, "Tehsil Topper" style titles |
| **Gallery** | Upload and delete photos, captions, categories |
| **Events** | Add events, mark them upcoming or completed |
| **Services** | Courses, batches and their tick-list points |
| **Faculty** | Director, co-director and teachers with qualifications |
| **Contact Info** | Address, phone numbers, email, timings, Google map |
| **Social Media** | Instagram, Facebook, YouTube, WhatsApp |
| **Messages** | Enquiries sent through the contact form |
| **Settings** | Site name, logo, announcement bar, your password |

## Common tasks

**Add a student result** — Results → enter name and percentage → choose photo →
**Save Result**. To fix a mistake later, press **Edit** in the table; the form at
the top fills in with that student's details.

**Add many photos at once** — Gallery → **Choose Photos** → select them all
(hold `Ctrl` while clicking, or `Ctrl+A` for a whole folder) → type a caption →
pick a category → **Upload**.

**Change the phone number** — Contact Info → edit → **Save**. It updates on the
contact page, in the footer of every page, and on the call and WhatsApp buttons
all at once.

**Hide the announcement bar** — Settings → untick *Show the announcement bar*.

## Photo guidance

Upload straight from your phone — the site shrinks photos automatically.

| | |
|---|---|
| Accepted types | JPG, JPEG, PNG, WEBP, GIF |
| Maximum file size | 8 MB per photo |
| Automatic resizing | Anything wider than 1600px is shrunk |

A 12 MP phone photo (about 2.3 MB) is stored at roughly 500 KB — a 79% saving,
so the site stays fast on mobile data.

**How many photos?** Keep the gallery to around **100**. It still works with
several hundred, but visitors on phone data will wait longer, because each
gallery tile currently downloads the full-size photo. Use the categories
(Classes, Events, Students, Results, Campus) so people can filter instead of
scrolling through everything.

**Space is not a concern** — 100 photos is about 25 MB.

## Things worth knowing

- When you edit an item and do **not** choose a new photo, the existing photo is kept.
- Deleting cannot be undone. The site asks you to confirm first.
- Leaving a field empty usually hides it — an empty second button, an empty map link.
- If a photo file goes missing, that item shows a "Photo coming soon" placeholder
  rather than a broken image.

## Backing up

Copy **two things** together:

1. `database.db` — all your text, results, events and settings
2. the `uploads/` folder — all your photos

That pair is your entire website. Copy them somewhere safe regularly.

---

# Part 2 — For a developer

## Running it

```bash
pip install -r requirements.txt
python app.py
```

The database and all seed content are created automatically on first run.

## Project structure

```
jk/
├── app.py              # Flask app: every route, public + admin
├── db.py               # SQLite schema, seed data, query helpers
├── image_utils.py      # Upload validation, saving, resizing, deleting
├── requirements.txt
├── start.bat           # One-click launcher for the owner
├── database.db         # Created on first run (git-ignored)
│
├── templates/
│   ├── base.html       # Public layout: navbar, footer, call/WhatsApp buttons
│   ├── _icons.html     # Inline SVG icon set, used as {{ icon('phone') }}
│   ├── index.html  results.html  services.html
│   ├── gallery.html  events.html  contact.html  404.html
│   └── admin/
│       ├── base.html   login.html   dashboard.html
│       ├── results.html  gallery.html  events.html
│       ├── services.html  faculty.html  messages.html
│       └── homepage.html  contact.html  social.html  settings.html
│
├── static/
│   ├── css/style.css   # Public site (design tokens in :root)
│   ├── css/admin.css   # Admin panel
│   ├── js/script.js    # Mobile menu, gallery filter, lightbox, fade-in
│   ├── js/admin.js     # Sidebar, edit-fills-form, image preview, delete confirm
│   └── images/         # backgroundImg.jpg, placeholder.svg, favicon.svg
│
└── uploads/            # Uploaded photos (git-ignored; filenames stored in SQLite)
```

## Database

Eight tables, no ORM — plain `sqlite3` with a `Row` factory:

`admins`, `settings`, `results`, `gallery`, `events`, `services`, `faculty`,
`messages`.

All editable page text lives in `settings` as key/value pairs. To add a new
editable field:

1. Add the key to `DEFAULT_SETTINGS` in `db.py`
2. Add an input with that `name` to the relevant admin template
3. Read it as `settings.your_key` in the public template

`save_settings_form()` only stores keys that exist in `DEFAULT_SETTINGS`, so
stray form fields never reach the database.

## Security

- Passwords hashed with Werkzeug's `generate_password_hash`; never stored plain.
- Session-based login; every `/admin/*` route sits behind `@login_required`.
- CSRF token verified on **every** POST via a `before_request` hook.
- Uploads validated on extension and size, renamed with a random suffix, and
  served from a dedicated route.
- `MAX_CONTENT_LENGTH` caps requests at 8 MB.

## Front-end notes

Mobile-first plain CSS; all colours and spacing are custom properties in
`:root`. Playfair Display is used for `h1`/`h2`; Poppins for everything else.

Two traps worth knowing before editing the grids:

- `.btn` keeps `white-space: normal`, and grid children carry `min-width: 0`.
  A non-wrapping button sets a min-content width that a grid column cannot
  shrink below, which pushes cards off-screen on phones.
- The card grids use explicit `repeat(N, 1fr)` with breakpoints, **not**
  `repeat(auto-fit, …)` — `auto-fit` collapses empty tracks, so a section
  holding one card stretches it across the entire row.

## Deploying

Set these environment variables in production:

```bash
SECRET_KEY=<a long random string>   # keeps logins valid across restarts
ADMIN_USERNAME=<username>           # only used when creating the first admin
ADMIN_PASSWORD=<password>
```

Then run behind a real WSGI server:

```bash
pip install waitress
waitress-serve --port=8000 app:app
```

Do not deploy with `debug=True`.

## Known limitations

- **No gallery thumbnails.** Tiles render at ~280px but download the full 1600px
  upload. Generating a thumbnail at upload time would cut the gallery's first
  load by roughly 10×; this is the main thing limiting the gallery past ~150 photos.
- **No gallery pagination** — every photo renders on one page.
- `backgroundImg.png` in the repo root is unused; the live hero image is
  `static/images/backgroundImg.jpg`.
