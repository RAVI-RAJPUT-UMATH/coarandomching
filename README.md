# JK Classes Barnagar — Website & Admin Panel

A complete, responsive website for JK Classes Barnagar with a simple admin panel,
so the whole site can be managed without touching any code.

**Tech:** Python Flask + SQLite + plain HTML/CSS/JavaScript. No React, no build step,
no Docker. Two dependencies in total.

---

## Part 1 — For the coaching owner

### Starting the website

1. Open the project folder.
2. Double-click `start.bat` (Windows). The website starts.
3. Open your browser at **http://127.0.0.1:5000**

### Logging in to the admin panel

Go to **http://127.0.0.1:5000/admin/login**

| | |
|---|---|
| Username | `admin` |
| Password | `jkclasses123` |

> **Change this password immediately.** In the admin panel go to
> **Settings → Change Your Password**.

### What you can change

Everything on the website. Pick a section from the blue menu on the left:

| Menu item | What it changes |
|---|---|
| **Dashboard** | Overview and shortcuts |
| **Homepage** | The big banner, About Us text, the four highlights, the numbers strip |
| **Results** | Student names, percentages, photos, "Tehsil Topper" style titles |
| **Gallery** | Upload and delete photos, add captions and categories |
| **Events** | Add events, mark them upcoming or completed |
| **Services** | Courses, batches and their bullet points |
| **Faculty** | Director, co-director and teachers with their qualifications |
| **Contact Info** | Address, phone numbers, email, timings, Google map |
| **Social Media** | Instagram, Facebook, YouTube and WhatsApp links |
| **Messages** | Enquiries people sent through the contact form |
| **Settings** | Website name, logo, announcement bar, your password |

### Adding a student result

Results → fill in **Student Name** and **Percentage** → choose the photo →
press **Save Result**. It appears on the website straight away.

To correct a mistake later, press **Edit** in the table. The form at the top fills
in with that student's details — change what you need and press Save again.

### Adding 20 photos at once

Gallery → **Choose Photos** → select all the photos together (hold `Ctrl` while
clicking, or `Ctrl+A` to pick every photo in a folder) → type a caption →
choose a category → press **Upload**. Done.

### Changing the phone number

Contact Info → change the number → **Save Contact Information**. It updates on the
contact page, in the footer of every page, and on the call and WhatsApp buttons
all at once.

### Things worth knowing

- Photos can be JPG, PNG or WEBP, up to 8 MB each. Large photos are shrunk
  automatically so the website stays fast on mobile data.
- When you edit an item and do **not** choose a new photo, the existing photo is kept.
- Deleting cannot be undone — the website asks you to confirm first.
- Leaving a field empty usually hides that piece from the website (for example an
  empty second button, or an empty map link).

---

## Part 2 — For a developer

### Running it

```bash
pip install -r requirements.txt
python app.py
```

The database and all seed content are created automatically on first run.

### Project structure

```
jk/
├── app.py              # Flask app: all routes, public + admin
├── db.py               # SQLite schema, seed data, query helpers
├── image_utils.py      # Upload validation, saving, resizing, deleting
├── requirements.txt
├── start.bat           # One-click launcher for the owner
├── database.db         # Created on first run (git-ignored)
│
├── templates/
│   ├── base.html       # Public layout: navbar, footer, WhatsApp/call buttons
│   ├── index.html      # Home
│   ├── results.html  services.html  gallery.html  events.html  contact.html
│   ├── 404.html
│   └── admin/
│       ├── base.html   # Admin layout with sidebar
│       ├── login.html  dashboard.html
│       ├── results.html  gallery.html  events.html  services.html  faculty.html
│       └── homepage.html  contact.html  social.html  settings.html  messages.html
│
├── static/
│   ├── css/style.css   # Public site
│   ├── css/admin.css   # Admin panel
│   ├── js/script.js    # Mobile menu, gallery filter, lightbox, fade-in
│   ├── js/admin.js     # Sidebar, edit-fills-form, image preview, delete confirm
│   └── images/         # placeholder.svg, favicon.svg
│
└── uploads/            # Uploaded photos (git-ignored, file names stored in SQLite)
```

### Database

Seven tables, no ORM — plain `sqlite3` with `Row` factory:

`admins`, `settings` (key/value for all editable text), `results`, `gallery`,
`events`, `services`, `faculty`, `messages`.

All editable page text lives in `settings`. To add a new editable field:
add the key to `DEFAULT_SETTINGS` in `db.py`, add an input with that `name` to the
relevant admin template, and read it as `settings.your_key` in a public template.
`save_settings_form()` only stores keys that exist in `DEFAULT_SETTINGS`, so stray
form fields never reach the database.

### Security

- Passwords hashed with Werkzeug's `generate_password_hash` (never stored in plain text).
- Session-based login; every `/admin/*` route is behind the `@login_required` decorator.
- CSRF token checked on **every** POST, via a `before_request` hook.
- Uploads validated on extension and size; files are renamed with a random suffix
  and served from a dedicated route.
- `MAX_CONTENT_LENGTH` caps request size at 8 MB.

### Deploying

Set these environment variables in production:

```bash
SECRET_KEY=<a long random string>      # keeps login sessions valid across restarts
ADMIN_USERNAME=<username>              # only used when creating the first admin
ADMIN_PASSWORD=<password>
```

Then run behind a real WSGI server, for example:

```bash
pip install waitress
waitress-serve --port=8000 app:app
```

Back up `database.db` and the `uploads/` folder together — that is the entire site content.
