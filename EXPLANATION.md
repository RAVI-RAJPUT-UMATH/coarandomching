# How This Website Works

A walkthrough of the JK Classes Barnagar project — what each piece does, why it
was built that way, and how a request travels through it.

Written for someone comfortable with Python basics who has not built a Flask app
before.

---

## 1. The idea in one paragraph

A coaching institute needs a website. The owner is a teacher, not a programmer.
So the site is split in two: a **public website** that visitors see, and an
**admin panel** where the owner edits everything — results, photos, events,
phone numbers — through ordinary forms. Nothing a visitor reads is written into
the code; it all comes out of a database that the admin panel writes to.

---

## 2. Why this technology

| Choice | Reason |
|---|---|
| **Flask** | Small. One file holds every route, readable top to bottom. |
| **SQLite** | The whole database is a single file, `database.db`. No server to install or configure. |
| **Plain HTML/CSS/JS** | No build step. Edit a file, refresh the browser. |
| **Only 2 dependencies** | Flask and Pillow. Less to break, less to update. |

No React, no Docker, no bundler. For a site of this size they would add work
without adding capability. Anyone who knows a little Python can maintain this.

---

## 3. The files

```
jk/
├── app.py            ← all the routes (the "what happens when you visit a URL")
├── db.py             ← database structure + starting content
├── image_utils.py    ← photo upload handling
├── database.db       ← the entire site's content (created on first run)
├── uploads/          ← uploaded photos
│
├── templates/        ← HTML pages
│   ├── base.html     ← the frame every public page sits inside
│   ├── _icons.html   ← reusable SVG icons
│   ├── index.html … contact.html
│   └── admin/        ← the admin panel's pages
│
└── static/
    ├── css/style.css ← public site styling
    ├── css/admin.css ← admin panel styling
    └── js/           ← mobile menu, gallery filter, lightbox
```

---

## 4. How a page gets built

Visitor opens `/results`. Here is the whole journey:

**Step 1 — Flask matches the URL.** In `app.py`:

```python
@app.route("/results")
def results_page():
    rows = all_results()
    return render_template("results.html",
                           featured=[r for r in rows if r["featured"]],
                           others=[r for r in rows if not r["featured"]])
```

**Step 2 — the data is fetched.** `all_results()` runs one SQL query, sorted so
toppers come first.

**Step 3 — the template fills in.** `results.html` loops over the rows:

```html
{% for r in others %}
  <h3>{{ r.name }}</h3>
  <span class="pct">{{ r.percentage }}</span>
{% endfor %}
```

**Step 4 — the frame wraps it.** `results.html` starts with
`{% extends "base.html" %}`, so it inherits the navbar, footer and WhatsApp
button without repeating them. This is **template inheritance** — write the
shared parts once.

**Step 5 — HTML goes to the browser**, which fetches `style.css` and the photos.

---

## 5. The database

Eight tables. Seven store content; one is unusual and worth understanding.

| Table | Holds |
|---|---|
| `admins` | Login username and hashed password |
| `settings` | **Every piece of editable text on the site** |
| `results` | Student name, percentage, photo, achievement |
| `gallery` | Photos with caption and category |
| `events` | Title, date, description, upcoming/completed |
| `services` | Courses and their bullet points |
| `faculty` | Teachers and qualifications |
| `messages` | Contact-form enquiries |

### The `settings` table

Instead of a column per field, it is a simple **key–value store**:

| key | value |
|---|---|
| `hero_heading` | The Wave of |
| `contact_phone_1` | 7489755479 |
| `about_text` | JK Classes in Barnagar is a specialised… |

Why? Because adding a new editable field needs no schema change. Add the key to
`DEFAULT_SETTINGS` in `db.py`, add a form input, and use it in a template. Three
small edits, no migration.

In templates it arrives as a plain dictionary:

```html
<a href="tel:{{ settings.contact_phone_1 }}">{{ settings.contact_phone_1 }}</a>
```

That single line is why changing the phone number once in the admin panel
updates it on the contact page, in the footer, and on the call button.

### No ORM

Queries are written in SQL directly:

```python
def query(sql, args=(), one=False):
    cur = get_db().execute(sql, args)
    rows = cur.fetchall()
    return (rows[0] if rows else None) if one else rows
```

Values always pass as `args`, never glued into the string with f-strings. SQLite
then treats them as data, not code — which is what prevents **SQL injection**.

---

## 6. Photo uploads

Handled in `image_utils.py`, in four steps:

1. **Check the extension** — only jpg, jpeg, png, webp, gif.
2. **Check the size** — reject anything over 8 MB, measured by seeking to the
   end of the stream rather than reading the file into memory.
3. **Rename it** — `secure_filename()` strips dangerous characters, then a random
   suffix is added: `photo-a3f9c21b45de.jpg`. This stops a second upload with the
   same name from overwriting the first, and stops anyone choosing their own path.
4. **Shrink it** — Pillow resizes anything wider than 1600px. A 12 MP phone photo
   drops from ~2.3 MB to ~500 KB, so the site stays fast on mobile data.

The database stores **only the filename**. The file itself lives in `uploads/`.
Templates never build that URL by hand; they use a filter:

```python
@app.template_filter("media")
def media_filter(filename):
    if upload_exists(filename):
        return url_for("uploaded_file", filename=filename)
    return url_for("static", filename="images/placeholder.svg")
```

The `upload_exists` check matters: if a file is ever deleted but its database row
survives, the page shows a "Photo coming soon" placeholder instead of a broken
image icon.

---

## 7. Login and security

### Passwords are never stored

```python
generate_password_hash("jkclasses123")
# 'scrypt:32768:8:1$Xy9...'  — one-way
```

You cannot reverse a hash. Logging in re-hashes what was typed and compares.
Even with the database file, the password cannot be read out.

### Protecting admin pages

A **decorator** wraps every admin route:

```python
def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin_id"):
            return redirect(url_for("admin_login", next=request.path))
        return view(*args, **kwargs)
    return wrapped
```

`session` is a cookie, cryptographically signed with `SECRET_KEY`, so a visitor
cannot edit it to claim they are logged in.

### CSRF protection

Without it, another site could make your browser silently POST to
`/admin/results/delete/3` while you are logged in. So every form carries a
secret token, and a hook checks it before any POST runs:

```python
@app.before_request
def check_csrf():
    if request.method == "POST":
        sent = request.form.get("csrf_token", "")
        if not sent or not secrets.compare_digest(sent, session.get("_csrf", "")):
            abort(400)
```

`compare_digest` compares in constant time, so the comparison itself leaks
nothing about the correct value.

---

## 8. The admin panel's editing pattern

Every section — results, events, services, faculty — uses the same shape:

- One form at the top of the page
- A table of existing entries below
- Pressing **Edit** fills the form with that row's values

Editing happens without a page reload. Each Edit button carries its row as JSON:

```html
<button data-edit='{"id": 3, "name": "Suraj", "percentage": "94%"}'>Edit</button>
```

and `admin.js` copies those values into the matching form fields. One form does
both "add" and "edit": a hidden `id` field is empty when adding, filled when
editing, and the route branches on it:

```python
if result_id:
    execute("UPDATE results SET … WHERE id=?", …)
else:
    execute("INSERT INTO results … ")
```

When editing without choosing a new photo, the old filename is kept — so the
owner can fix a typo without re-uploading the picture.

---

## 9. The front-end JavaScript

About 160 lines, no libraries, four jobs:

1. **Mobile menu** — toggles the `hidden` attribute on the nav.
2. **Gallery filter** — hides non-matching photos by category.
3. **Lightbox** — builds the overlay in JS, supports arrow keys and Escape.
4. **Fade-in** — `IntersectionObserver` adds a class when a section scrolls into
   view, with a fallback that simply shows everything if the browser is old.

All of it is progressive: with JavaScript disabled the pages still render and
every link still works.

---

## 10. How it stays responsive

Mobile-first: base CSS targets phones, `@media (min-width: …)` adds columns as
the screen grows. Gallery goes 2 → 3 → 4 columns; cards go 1 → 2 → 3/4.

Two subtle traps this project hit, both worth knowing:

**Buttons must be allowed to wrap.** A button with `white-space: nowrap`
establishes a minimum width, and because grid items default to
`min-width: auto`, the column cannot shrink below it. Result: cards pushed off
the screen edge. Fix — let buttons wrap, and set `min-width: 0` on grid children.

**`repeat(auto-fit, …)` collapses empty columns.** In a three-column section
holding one card, `auto-fit` removes the two empty tracks and stretches that
card across the whole row. Explicit `repeat(3, 1fr)` keeps it one-third wide.

---

## 11. Ideas if you extend it

- **Thumbnails.** Gallery tiles display ~280px wide but download the full
  1600px file. Generating a small copy at upload would cut the gallery's first
  load by roughly 10×. This is the main thing limiting the gallery past ~150 photos.
- **Pagination** on the gallery once photos pass a few hundred.
- **Email on enquiry**, so the owner is notified instead of checking the panel.
- **Backups.** `database.db` plus `uploads/` is the entire site. Copy both.

---

## 12. Glossary

| Term | Meaning |
|---|---|
| **Route** | A URL mapped to a Python function |
| **Template** | An HTML file with placeholders Flask fills in |
| **Jinja** | The template language — `{{ value }}`, `{% for %}` |
| **Template inheritance** | Shared layout in `base.html`, pages fill in the gaps |
| **Decorator** | A function wrapping another to add behaviour, e.g. `@login_required` |
| **Session** | Signed cookie remembering who is logged in |
| **Hash** | One-way scramble of a password |
| **CSRF** | Attack where another site posts to yours using your login |
| **Migration** | Changing the database structure after data exists |
