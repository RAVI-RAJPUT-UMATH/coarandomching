"""
JK Classes Barnagar - website + admin panel.

Run it with:

    pip install -r requirements.txt
    python app.py

Then open http://127.0.0.1:5000  (admin panel: /admin/login)
"""

import os
import secrets
from datetime import date, datetime
from functools import wraps

from flask import (Flask, abort, flash, redirect, render_template, request,
                   send_from_directory, session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

import db
from db import execute, get_settings, query, set_setting
from image_utils import delete_upload, save_upload

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)

# --- configuration -----------------------------------------------------------
# SECRET_KEY keeps the login session secure. On a real server set it as an
# environment variable so it stays the same between restarts.
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY") or "jk-classes-barnagar-dev-key"
if os.environ.get("VERCEL"):
    app.config["UPLOAD_FOLDER"] = "/tmp/uploads"
else:
    app.config["UPLOAD_FOLDER"] = os.path.join(BASE_DIR, "uploads")
app.config["MAX_CONTENT_LENGTH"] = 3 * 1024 * 1024          # 8 MB per upload
app.config["ADMIN_USERNAME"] = os.environ.get("ADMIN_USERNAME", "admin")
app.config["ADMIN_PASSWORD"] = os.environ.get("ADMIN_PASSWORD", "jkclasses123")

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
app.teardown_appcontext(db.close_db)


# ---------------------------------------------------------------- CSRF tokens

def csrf_token():
    """A per-session token that every admin form must send back."""
    if "_csrf" not in session:
        session["_csrf"] = secrets.token_urlsafe(32)
    return session["_csrf"]


@app.before_request
def check_csrf():
    if request.method == "POST":
        sent = request.form.get("csrf_token", "")
        if not sent or not secrets.compare_digest(sent, session.get("_csrf", "")):
            abort(400, "Your form session expired. Please go back and try again.")


# --------------------------------------------------------------- template glue

@app.context_processor
def inject_globals():
    """Values every template can use without each route passing them in."""
    site = get_settings()

    # The hero/CTA photo: whatever the owner uploaded in Admin > Homepage,
    # otherwise the background image that ships with the site.
    if upload_exists(site.get("hero_image")):
        hero_bg = url_for("uploaded_file", filename=site["hero_image"])
    else:
        hero_bg = url_for("static", filename="images/backgroundImg.jpg")

    return {
        "settings": site,
        "hero_bg": hero_bg,
        "csrf_token": csrf_token,
        "gallery_categories": db.GALLERY_CATEGORIES,
        "current_path": request.path,
        "now_year": date.today().year,
    }


@app.template_filter("lines")
def lines_filter(text):
    """Turn a multi-line textarea value into a list of non-empty lines."""
    if not text:
        return []
    return [line.strip() for line in str(text).splitlines() if line.strip()]


@app.template_filter("day")
def day_filter(value):
    """'2026-01-15' -> '15'. Falls back to the raw text for anything else."""
    try:
        return datetime.strptime(str(value)[:10], "%Y-%m-%d").strftime("%d")
    except (ValueError, TypeError):
        return str(value or "")[:2]


@app.template_filter("monthyear")
def monthyear_filter(value):
    """'2026-01-15' -> 'Jan 2026'. Used by the date badge on event photos."""
    try:
        return datetime.strptime(str(value)[:10], "%Y-%m-%d").strftime("%b %Y")
    except (ValueError, TypeError):
        return ""


def upload_exists(filename):
    """True when an uploaded file is still present on disk."""
    if not filename:
        return False
    return os.path.isfile(os.path.join(app.config["UPLOAD_FOLDER"], os.path.basename(filename)))


@app.template_filter("media")
def media_filter(filename):
    """
    URL for an uploaded file, or the placeholder image.

    The file is checked before it is linked, so a record left pointing at a
    picture that is no longer on disk shows the placeholder instead of a
    broken image.
    """
    if upload_exists(filename):
        return url_for("uploaded_file", filename=filename)
    return url_for("static", filename="images/placeholder.svg")


@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


# ------------------------------------------------------------- data shortcuts

def all_results():
    return query("SELECT * FROM results ORDER BY featured DESC, sort_order ASC, id ASC")


def all_gallery():
    return query("SELECT * FROM gallery ORDER BY sort_order ASC, id DESC")


def all_events():
    """Upcoming events first (soonest at the top), then past events (newest first)."""
    return query(
        "SELECT * FROM events ORDER BY "
        "  CASE status WHEN 'upcoming' THEN 0 ELSE 1 END, "
        "  CASE status WHEN 'upcoming' THEN event_date END ASC, "
        "  CASE status WHEN 'upcoming' THEN NULL ELSE event_date END DESC, "
        "  id DESC"
    )


def all_services():
    return query("SELECT * FROM services ORDER BY sort_order ASC, id ASC")


def all_faculty():
    return query("SELECT * FROM faculty ORDER BY sort_order ASC, id ASC")


# ------------------------------------------------------------- public website

@app.route("/")
def index():
    return render_template(
        "index.html",
        page_title="JK Classes Barnagar | Coaching for Class 6th to 12th",
        results=all_results()[:6],
        services=all_services()[:4],
        events=all_events()[:3],
        gallery=all_gallery()[:6],
        faculty=all_faculty(),
    )


@app.route("/results")
def results_page():
    rows = all_results()
    return render_template(
        "results.html",
        page_title="Student Results | JK Classes Barnagar",
        featured=[r for r in rows if r["featured"]],
        others=[r for r in rows if not r["featured"]],
        total=len(rows),
    )


@app.route("/services")
def services_page():
    return render_template(
        "services.html",
        page_title="Courses and Services | JK Classes Barnagar",
        services=all_services(),
        faculty=all_faculty(),
    )


@app.route("/gallery")
def gallery_page():
    photos = all_gallery()
    used = [c for c in db.GALLERY_CATEGORIES if any(p["category"] == c for p in photos)]
    return render_template(
        "gallery.html",
        page_title="Photo Gallery | JK Classes Barnagar",
        photos=photos,
        categories=used,
    )


@app.route("/events")
def events_page():
    rows = all_events()
    return render_template(
        "events.html",
        page_title="Events | JK Classes Barnagar",
        upcoming=[e for e in rows if e["status"] == "upcoming"],
        completed=[e for e in rows if e["status"] != "upcoming"],
    )


@app.route("/contact", methods=["GET", "POST"])
def contact_page():
    if request.method == "POST":
        f = request.form
        if not f.get("first_name", "").strip() or not f.get("message", "").strip():
            flash("Please enter your name and a message.", "error")
        else:
            execute(
                "INSERT INTO messages (first_name, last_name, email, phone, message)"
                " VALUES (?, ?, ?, ?, ?)",
                (f.get("first_name", "").strip(), f.get("last_name", "").strip(),
                 f.get("email", "").strip(), f.get("phone", "").strip(),
                 f.get("message", "").strip()),
            )
            flash("Thank you! Your message has been sent. We will get back to you soon.", "success")
            return redirect(url_for("contact_page"))
    return render_template("contact.html", page_title="Contact Us | JK Classes Barnagar")


@app.errorhandler(404)
def not_found(_e):
    return render_template("404.html", page_title="Page not found"), 404


@app.errorhandler(413)
def too_large(_e):
    flash("That file is too large. Please upload an image under 8 MB.", "error")
    return redirect(request.referrer or url_for("admin_dashboard"))


# ------------------------------------------------------------------ admin auth

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin_id"):
            flash("Please log in to continue.", "error")
            return redirect(url_for("admin_login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


@app.route("/admin")
def admin_root():
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if session.get("admin_id"):
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        admin = query("SELECT * FROM admins WHERE username = ?", (username,), one=True)
        if admin and check_password_hash(admin["password_hash"], password):
            session.clear()
            session["admin_id"] = admin["id"]
            session["admin_name"] = admin["username"]
            return redirect(request.args.get("next") or url_for("admin_dashboard"))
        flash("Wrong username or password. Please try again.", "error")

    return render_template("admin/login.html", page_title="Admin Login | JK Classes")


@app.route("/admin/logout")
def admin_logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("admin_login"))


@app.route("/admin/dashboard")
@login_required
def admin_dashboard():
    counts = {
        "results": query("SELECT COUNT(*) c FROM results", one=True)["c"],
        "gallery": query("SELECT COUNT(*) c FROM gallery", one=True)["c"],
        "events": query("SELECT COUNT(*) c FROM events", one=True)["c"],
        "services": query("SELECT COUNT(*) c FROM services", one=True)["c"],
        "faculty": query("SELECT COUNT(*) c FROM faculty", one=True)["c"],
        "messages": query("SELECT COUNT(*) c FROM messages WHERE is_read = 0", one=True)["c"],
    }
    return render_template(
        "admin/dashboard.html",
        page_title="Dashboard | JK Classes Admin",
        counts=counts,
        recent_messages=query("SELECT * FROM messages ORDER BY id DESC LIMIT 5"),
    )


# ---------------------------------------------------------------- admin: results

@app.route("/admin/results")
@login_required
def admin_results():
    return render_template("admin/results.html", page_title="Results | JK Classes Admin",
                           results=all_results())


@app.route("/admin/results/save", methods=["POST"])
@login_required
def admin_results_save():
    f = request.form
    result_id = f.get("id", "").strip()
    name = f.get("name", "").strip()
    percentage = f.get("percentage", "").strip()

    if not name or not percentage:
        flash("Student name and percentage are required.", "error")
        return redirect(url_for("admin_results"))

    photo = save_upload(request.files.get("photo"))
    fields = (name, percentage, f.get("achievement", "").strip(), f.get("class_name", "").strip(),
              f.get("year", "").strip(), 1 if f.get("featured") else 0,
              int(f.get("sort_order") or 0))

    if result_id:
        old = query("SELECT * FROM results WHERE id = ?", (result_id,), one=True)
        if not old:
            abort(404)
        if photo:
            delete_upload(old["photo"])
        execute(
            "UPDATE results SET name=?, percentage=?, achievement=?, class_name=?, year=?,"
            " featured=?, sort_order=?, photo=? WHERE id=?",
            fields + (photo or old["photo"], result_id),
        )
        flash("Result updated.", "success")
    else:
        execute(
            "INSERT INTO results (name, percentage, achievement, class_name, year, featured,"
            " sort_order, photo) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            fields + (photo,),
        )
        flash("Result added.", "success")
    return redirect(url_for("admin_results"))


@app.route("/admin/results/delete/<int:result_id>", methods=["POST"])
@login_required
def admin_results_delete(result_id):
    row = query("SELECT * FROM results WHERE id = ?", (result_id,), one=True)
    if row:
        delete_upload(row["photo"])
        execute("DELETE FROM results WHERE id = ?", (result_id,))
        flash("Result deleted.", "success")
    return redirect(url_for("admin_results"))


# ---------------------------------------------------------------- admin: gallery

@app.route("/admin/gallery")
@login_required
def admin_gallery():
    return render_template("admin/gallery.html", page_title="Gallery | JK Classes Admin",
                           photos=all_gallery())


@app.route("/admin/gallery/upload", methods=["POST"])
@login_required
def admin_gallery_upload():
    files = request.files.getlist("photos")
    title = request.form.get("title", "").strip()
    category = request.form.get("category", "Other")

    saved = 0
    for file in files:
        filename = save_upload(file)
        if filename:
            execute("INSERT INTO gallery (title, category, photo) VALUES (?, ?, ?)",
                    (title, category, filename))
            saved += 1

    if saved:
        flash(f"{saved} photo(s) uploaded.", "success")
    else:
        flash("No photo was uploaded. Please choose JPG, PNG or WEBP files under 8 MB.", "error")
    return redirect(url_for("admin_gallery"))


@app.route("/admin/gallery/update/<int:photo_id>", methods=["POST"])
@login_required
def admin_gallery_update(photo_id):
    execute("UPDATE gallery SET title = ?, category = ? WHERE id = ?",
            (request.form.get("title", "").strip(),
             request.form.get("category", "Other"), photo_id))
    flash("Photo details saved.", "success")
    return redirect(url_for("admin_gallery"))


@app.route("/admin/gallery/delete/<int:photo_id>", methods=["POST"])
@login_required
def admin_gallery_delete(photo_id):
    row = query("SELECT * FROM gallery WHERE id = ?", (photo_id,), one=True)
    if row:
        delete_upload(row["photo"])
        execute("DELETE FROM gallery WHERE id = ?", (photo_id,))
        flash("Photo deleted.", "success")
    return redirect(url_for("admin_gallery"))


# ----------------------------------------------------------------- admin: events

@app.route("/admin/events")
@login_required
def admin_events():
    return render_template("admin/events.html", page_title="Events | JK Classes Admin",
                           events=all_events())


@app.route("/admin/events/save", methods=["POST"])
@login_required
def admin_events_save():
    f = request.form
    event_id = f.get("id", "").strip()
    title = f.get("title", "").strip()
    if not title:
        flash("Event title is required.", "error")
        return redirect(url_for("admin_events"))

    image = save_upload(request.files.get("image"))
    fields = (title, f.get("event_date", "").strip(), f.get("description", "").strip(),
              f.get("location", "").strip(), f.get("button_text", "").strip(),
              f.get("button_link", "").strip(),
              "upcoming" if f.get("status") == "upcoming" else "completed")

    if event_id:
        old = query("SELECT * FROM events WHERE id = ?", (event_id,), one=True)
        if not old:
            abort(404)
        if image:
            delete_upload(old["image"])
        execute(
            "UPDATE events SET title=?, event_date=?, description=?, location=?, button_text=?,"
            " button_link=?, status=?, image=? WHERE id=?",
            fields + (image or old["image"], event_id),
        )
        flash("Event updated.", "success")
    else:
        execute(
            "INSERT INTO events (title, event_date, description, location, button_text,"
            " button_link, status, image) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            fields + (image,),
        )
        flash("Event added.", "success")
    return redirect(url_for("admin_events"))


@app.route("/admin/events/delete/<int:event_id>", methods=["POST"])
@login_required
def admin_events_delete(event_id):
    row = query("SELECT * FROM events WHERE id = ?", (event_id,), one=True)
    if row:
        delete_upload(row["image"])
        execute("DELETE FROM events WHERE id = ?", (event_id,))
        flash("Event deleted.", "success")
    return redirect(url_for("admin_events"))


# --------------------------------------------------------------- admin: services

@app.route("/admin/services")
@login_required
def admin_services():
    return render_template("admin/services.html", page_title="Services | JK Classes Admin",
                           services=all_services())


@app.route("/admin/services/save", methods=["POST"])
@login_required
def admin_services_save():
    f = request.form
    service_id = f.get("id", "").strip()
    title = f.get("title", "").strip()
    if not title:
        flash("Service title is required.", "error")
        return redirect(url_for("admin_services"))

    image = save_upload(request.files.get("image"))
    fields = (title, f.get("subtitle", "").strip(), f.get("description", "").strip(),
              f.get("points", "").strip(), f.get("button_text", "").strip(),
              f.get("button_link", "").strip(), int(f.get("sort_order") or 0))

    if service_id:
        old = query("SELECT * FROM services WHERE id = ?", (service_id,), one=True)
        if not old:
            abort(404)
        if image:
            delete_upload(old["image"])
        execute(
            "UPDATE services SET title=?, subtitle=?, description=?, points=?, button_text=?,"
            " button_link=?, sort_order=?, image=? WHERE id=?",
            fields + (image or old["image"], service_id),
        )
        flash("Service updated.", "success")
    else:
        execute(
            "INSERT INTO services (title, subtitle, description, points, button_text,"
            " button_link, sort_order, image) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            fields + (image,),
        )
        flash("Service added.", "success")
    return redirect(url_for("admin_services"))


@app.route("/admin/services/delete/<int:service_id>", methods=["POST"])
@login_required
def admin_services_delete(service_id):
    row = query("SELECT * FROM services WHERE id = ?", (service_id,), one=True)
    if row:
        delete_upload(row["image"])
        execute("DELETE FROM services WHERE id = ?", (service_id,))
        flash("Service deleted.", "success")
    return redirect(url_for("admin_services"))


# ---------------------------------------------------------------- admin: faculty

@app.route("/admin/faculty")
@login_required
def admin_faculty():
    return render_template("admin/faculty.html", page_title="Faculty | JK Classes Admin",
                           faculty=all_faculty())


@app.route("/admin/faculty/save", methods=["POST"])
@login_required
def admin_faculty_save():
    f = request.form
    faculty_id = f.get("id", "").strip()
    name = f.get("name", "").strip()
    if not name:
        flash("Name is required.", "error")
        return redirect(url_for("admin_faculty"))

    photo = save_upload(request.files.get("photo"))
    fields = (name, f.get("role", "").strip(), f.get("qualifications", "").strip(),
              f.get("bio", "").strip(), int(f.get("sort_order") or 0))

    if faculty_id:
        old = query("SELECT * FROM faculty WHERE id = ?", (faculty_id,), one=True)
        if not old:
            abort(404)
        if photo:
            delete_upload(old["photo"])
        execute(
            "UPDATE faculty SET name=?, role=?, qualifications=?, bio=?, sort_order=?, photo=?"
            " WHERE id=?",
            fields + (photo or old["photo"], faculty_id),
        )
        flash("Faculty member updated.", "success")
    else:
        execute(
            "INSERT INTO faculty (name, role, qualifications, bio, sort_order, photo)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            fields + (photo,),
        )
        flash("Faculty member added.", "success")
    return redirect(url_for("admin_faculty"))


@app.route("/admin/faculty/delete/<int:faculty_id>", methods=["POST"])
@login_required
def admin_faculty_delete(faculty_id):
    row = query("SELECT * FROM faculty WHERE id = ?", (faculty_id,), one=True)
    if row:
        delete_upload(row["photo"])
        execute("DELETE FROM faculty WHERE id = ?", (faculty_id,))
        flash("Faculty member deleted.", "success")
    return redirect(url_for("admin_faculty"))


# ----------------------------------------------- admin: homepage / contact / social

# Image settings are handled separately because they arrive as file uploads.
IMAGE_SETTINGS = ("hero_image", "about_image", "logo")


def save_settings_form():
    """Store every text field posted, plus any image fields that were uploaded.

    Only keys the site actually knows about are saved, so stray form fields
    (csrf_token, remove_* checkboxes, ...) never end up in the settings table.
    """
    known = db.DEFAULT_SETTINGS
    for key, value in request.form.items():
        if key in IMAGE_SETTINGS or key not in known:
            continue
        set_setting(key, value.strip())

    # A checkbox sends nothing at all when it is unticked, so each form lists
    # its checkbox names in hidden "_checkboxes" fields and we resolve them here.
    for key in request.form.getlist("_checkboxes"):
        if key in known:
            set_setting(key, "1" if request.form.get(key) else "0")

    current = get_settings()
    for key in IMAGE_SETTINGS:
        if key in request.files:
            filename = save_upload(request.files.get(key))
            if filename:
                delete_upload(current.get(key))
                set_setting(key, filename)
        if request.form.get("remove_" + key):
            delete_upload(current.get(key))
            set_setting(key, "")


@app.route("/admin/homepage", methods=["GET", "POST"])
@login_required
def admin_homepage():
    if request.method == "POST":
        save_settings_form()
        flash("Homepage content saved.", "success")
        return redirect(url_for("admin_homepage"))
    return render_template("admin/homepage.html", page_title="Homepage | JK Classes Admin")


@app.route("/admin/contact", methods=["GET", "POST"])
@login_required
def admin_contact():
    if request.method == "POST":
        save_settings_form()
        flash("Contact information saved.", "success")
        return redirect(url_for("admin_contact"))
    return render_template("admin/contact.html", page_title="Contact Info | JK Classes Admin")


@app.route("/admin/social", methods=["GET", "POST"])
@login_required
def admin_social():
    if request.method == "POST":
        save_settings_form()
        flash("Social media links saved.", "success")
        return redirect(url_for("admin_social"))
    return render_template("admin/social.html", page_title="Social Media | JK Classes Admin")


@app.route("/admin/messages")
@login_required
def admin_messages():
    rows = query("SELECT * FROM messages ORDER BY id DESC")
    execute("UPDATE messages SET is_read = 1 WHERE is_read = 0")
    return render_template("admin/messages.html", page_title="Messages | JK Classes Admin",
                           messages=rows)


@app.route("/admin/messages/delete/<int:message_id>", methods=["POST"])
@login_required
def admin_messages_delete(message_id):
    execute("DELETE FROM messages WHERE id = ?", (message_id,))
    flash("Message deleted.", "success")
    return redirect(url_for("admin_messages"))


@app.route("/admin/settings", methods=["GET", "POST"])
@login_required
def admin_settings():
    if request.method == "POST":
        if request.form.get("form") == "password":
            current = request.form.get("current_password", "")
            new = request.form.get("new_password", "")
            confirm = request.form.get("confirm_password", "")
            admin = query("SELECT * FROM admins WHERE id = ?", (session["admin_id"],), one=True)

            if not check_password_hash(admin["password_hash"], current):
                flash("Your current password is not correct.", "error")
            elif len(new) < 6:
                flash("The new password must be at least 6 characters long.", "error")
            elif new != confirm:
                flash("The two new passwords do not match.", "error")
            else:
                execute("UPDATE admins SET password_hash = ? WHERE id = ?",
                        (generate_password_hash(new), admin["id"]))
                flash("Password changed successfully.", "success")
        else:
            save_settings_form()
            flash("Site settings saved.", "success")
        return redirect(url_for("admin_settings"))

    return render_template("admin/settings.html", page_title="Settings | JK Classes Admin",
                           admin=query("SELECT * FROM admins WHERE id = ?",
                                       (session["admin_id"],), one=True))


# ------------------------------------------------------------------------ main

with app.app_context():
    db.init_db(app)

if __name__ == "__main__":
    print(" * JK Classes website running on http://127.0.0.1:5000")
    print(" * Admin panel: http://127.0.0.1:5000/admin/login")
    print(f" * Default login: {app.config['ADMIN_USERNAME']} / {app.config['ADMIN_PASSWORD']}")
    app.run(debug=True)
