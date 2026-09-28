# CLAUDE.md

Guidance for Claude Code when working in this repository.

## What this is

A website + admin panel for **JK Classes Barnagar**, a coaching institute in
Madhya Pradesh. The owner is **not a developer**: everything visitors see must
stay editable from `/admin` without touching code or the database.

Flask + SQLite + plain HTML/CSS/vanilla JS. Two dependencies. No build step,
no bundler, no framework. Keep it that way.

## Commands

```bash
pip install -r requirements.txt
python app.py                # http://127.0.0.1:5000  (admin at /admin/login)
```

Default admin login: `admin` / `jkclasses123` (changeable in Admin → Settings).

There is no test runner in the repo. Ad-hoc scripts live in the session
scratchpad; see "Testing" below for how to write them safely.

## Architecture

| File | Role |
|---|---|
| `app.py` | Every route, public + admin. Config, CSRF, template filters. |
| `db.py` | Schema, seed data, `query()` / `execute()` helpers. Plain `sqlite3`. |
| `image_utils.py` | Upload validation, saving, resizing, deletion. |
| `templates/base.html` | Public layout: navbar, footer, floating call/WhatsApp. |
| `templates/_icons.html` | `{% from "_icons.html" import icon %}` — inline SVG set. |
| `templates/admin/base.html` | Admin layout with sidebar. |
| `static/css/style.css` | Public site. All tokens in `:root` at the top. |
| `static/css/admin.css` | Admin panel. |

Eight tables: `admins`, `settings`, `results`, `gallery`, `events`, `services`,
`faculty`, `messages`.

## Rules that matter

**Never hardcode visitor-facing content.** Every heading, phone number, address
and image belongs in the `settings` table or a content table. If you add a
string to a template that the owner might want to change, you have created a
bug. To add an editable field:

1. Add the key to `DEFAULT_SETTINGS` in `db.py`
2. Add an input with that exact `name` to the relevant `templates/admin/*.html`
3. Read it as `settings.your_key` in the public template

`save_settings_form()` only stores keys present in `DEFAULT_SETTINGS`, so stray
fields (`csrf_token`, `remove_*`) never reach the database. A checkbox sends
nothing when unticked, so each form lists its checkbox names in hidden
`_checkboxes` inputs.

**Images are referenced by filename only.** Files live in `uploads/`, the
database stores the bare filename. Always render through the `media` filter —
it checks the file exists and falls back to `placeholder.svg`, so a record
pointing at a deleted file degrades gracefully instead of showing a broken
image. Never build an upload URL by hand.

**Every POST is CSRF-checked** by a `before_request` hook. Any new form needs
`<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">` or it will
400.

**Every `/admin/*` route needs `@login_required`.** Deletes are POST-only.

## CSS conventions

Mobile-first, plain CSS, no preprocessor. Design tokens are CSS custom
properties in `:root` — change colours and spacing there, not inline.

Two gotchas this codebase has already been bitten by; do not reintroduce them:

- **`.btn` must keep `white-space: normal`.** A non-wrapping button sets a
  min-content width that a grid column cannot shrink below, which pushes cards
  off-screen on phones. Grid children carry `min-width: 0` for the same reason.
- **Do not use `repeat(auto-fit, …)` for the card grids.** `auto-fit` collapses
  empty tracks, so a section with one card stretches it across the full row.
  Use explicit `repeat(N, 1fr)` with breakpoints. Where a short row should be
  centred instead of left-hugging, add the `grid--few` / `results-page-grid--few`
  modifier from the template based on item count.

Chips and pills placed directly inside `.card__body` (a column flex container)
need `align-self: flex-start`, or they stretch to full width.

All dark blue page bands share `--band-h` so they are the same depth sitewide.

Typography: Playfair Display for `h1`/`h2` only; Poppins for everything else.
Small headings stay on the sans — a Didone serif loses legibility at 14–16px.

## Testing

**Never run a destructive test against `database.db`.** The owner may be using
the admin panel at the same time; a backup-and-restore cycle will silently
discard whatever they uploaded during the window. Point the app at a sandbox:

```python
import db
db.DB_PATH = os.path.join(tempfile.mkdtemp(), "test.db")
import app as application          # must be imported AFTER patching DB_PATH
application.app.config["UPLOAD_FOLDER"] = <sandbox>/uploads
```

**Never bulk-delete from `uploads/`.** Real photos live beside any test files.
Delete only files you can prove are orphaned, and check the `settings` table
(`hero_image`, `about_image`, `logo`) as well as the five content tables —
missing that is how a real About photo was lost once.

Playwright is available and is the right tool for layout claims. Measure
`scrollWidth` vs `clientWidth` for overflow rather than eyeballing screenshots.
When checking for broken images, filter on `img.getAttribute('src') &&
img.complete && img.naturalWidth === 0` — lazy images below the fold are not
`complete` yet, and the lightbox deliberately holds one `<img>` with no `src`.

## Known state

- `backgroundImg.png` in the repo root is unused. The live hero image is
  `static/images/backgroundImg.jpg`.
- Gallery has no pagination and no thumbnails: tiles render at ~280px but
  download the full 1600px upload. Fine to roughly 100–150 photos; beyond that
  generate thumbnails before adding more.
- Seed gallery rows 1–9 have empty `photo` values and show the placeholder.
