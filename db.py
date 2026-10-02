"""
Database helpers for the JK Classes Barnagar website.

Plain sqlite3 (no ORM) so the whole data layer stays readable for a
beginner/intermediate developer. Every table is created on first run and
seeded with the institute's current information, which the owner can then
change from the admin panel.
"""

import os
import sqlite3
from datetime import date

from flask import g
from werkzeug.security import generate_password_hash

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
if os.environ.get("VERCEL"):
    DB_PATH = "/tmp/database.db"
else:
    DB_PATH = os.path.join(BASE_DIR, "database.db")


# ---------------------------------------------------------------- connection

def get_db():
    """One connection per request, stored on Flask's `g` object."""
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def query(sql, args=(), one=False):
    cur = get_db().execute(sql, args)
    rows = cur.fetchall()
    cur.close()
    return (rows[0] if rows else None) if one else rows


def execute(sql, args=()):
    db = get_db()
    cur = db.execute(sql, args)
    db.commit()
    last_id = cur.lastrowid
    cur.close()
    return last_id


# -------------------------------------------------------------------- schema

SCHEMA = """
CREATE TABLE IF NOT EXISTS admins (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL
);

-- Simple key/value store for every piece of editable site text.
CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS results (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    percentage  TEXT NOT NULL,
    achievement TEXT DEFAULT '',
    class_name  TEXT DEFAULT '',
    year        TEXT DEFAULT '',
    photo       TEXT DEFAULT '',
    featured    INTEGER NOT NULL DEFAULT 0,
    sort_order  INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS gallery (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    title      TEXT DEFAULT '',
    category   TEXT DEFAULT 'Other',
    photo      TEXT NOT NULL DEFAULT '',
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT NOT NULL,
    event_date  TEXT DEFAULT '',
    description TEXT DEFAULT '',
    location    TEXT DEFAULT '',
    image       TEXT DEFAULT '',
    button_text TEXT DEFAULT '',
    button_link TEXT DEFAULT '',
    status      TEXT NOT NULL DEFAULT 'upcoming',
    created_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS services (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT NOT NULL,
    subtitle    TEXT DEFAULT '',
    description TEXT DEFAULT '',
    points      TEXT DEFAULT '',
    image       TEXT DEFAULT '',
    button_text TEXT DEFAULT '',
    button_link TEXT DEFAULT '',
    sort_order  INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS faculty (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    name           TEXT NOT NULL,
    role           TEXT DEFAULT '',
    qualifications TEXT DEFAULT '',
    bio            TEXT DEFAULT '',
    photo          TEXT DEFAULT '',
    sort_order     INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS messages (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT DEFAULT '',
    last_name  TEXT DEFAULT '',
    email      TEXT DEFAULT '',
    phone      TEXT DEFAULT '',
    message    TEXT DEFAULT '',
    is_read    INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


# ------------------------------------------------------------ default content

DEFAULT_SETTINGS = {
    # Brand
    "site_name": "JK Classes Barnagar",
    "site_tagline": "Specialised coaching for classes 6th to 12th",
    "logo": "",
    "announcement": "Admissions open for 2025-26 - classes 6th to 12th, all subjects. Call 7489755479",
    "announcement_active": "1",

    # Hero
    "hero_heading": "The Wave of",
    "hero_highlight": "Education",
    "hero_subheading": ("JK Classes in Barnagar is a specialised coaching centre dedicated to "
                        "academic excellence and comprehensive exam preparation."),
    "hero_image": "",
    "hero_btn_text": "Learn More",
    "hero_btn_link": "/services",
    "hero_btn2_text": "Contact Us",
    "hero_btn2_link": "/contact",

    # Highlight strip under the hero
    "highlight_1_title": "6th to 12th",
    "highlight_1_text": "All Subjects",
    "highlight_2_title": "Experienced",
    "highlight_2_text": "Faculty",
    "highlight_3_title": "Result Driven",
    "highlight_3_text": "Approach",
    "highlight_4_title": "Personal Attention",
    "highlight_4_text": "and Guidance",

    # About
    "about_title": "JK CLASSES BARNAGAR",
    "about_text": ("JK Classes in Barnagar is a specialised coaching centre dedicated to academic "
                   "excellence and comprehensive exam preparation. We aim to build strong concepts, "
                   "confidence and bright futures for every student who walks through our doors."),
    "about_quote": "Education is the key to unlock the golden door of freedom.",
    "about_quote_by": "Jitendra Kumar Verma",
    "about_image": "",

    # Stats strip
    "stat_1_value": "6+",
    "stat_1_label": "Years of Experience",
    "stat_2_value": "500+",
    "stat_2_label": "Happy Students",
    "stat_3_value": "95%",
    "stat_3_label": "Success Rate",
    "stat_4_value": "Expert",
    "stat_4_label": "Faculty Team",

    # Results banner
    "results_heading": "CBSE CLASS 10TH RESULT 2025-26",
    "results_subheading": "We gave the Tehsil Topper",

    # Contact
    "contact_address": "34 D, Vyas Colony, Barnagar, Near Hanuman Mandir, Madhya Pradesh 456771",
    "contact_phone_1": "7489755479",
    "contact_phone_2": "9755272767",
    "contact_email": "jkclassesbarnagar@gmail.com",
    "contact_hours": "Monday to Sunday, 4:00 PM - 8:00 PM",
    "whatsapp_number": "7489755479",
    "map_embed": "https://www.google.com/maps?q=Barnagar%2C+Madhya+Pradesh+456771&output=embed",

    # Social
    "social_instagram": "https://www.instagram.com/officialjkclasses",
    "social_facebook": "",
    "social_youtube": "",

    # SEO
    "meta_description": ("JK Classes Barnagar - coaching for classes 6th to 12th in Science, "
                         "Commerce and Humanities. Special batches for class 10th, 12th and JNVST."),
}


SEED_RESULTS = [
    # name, percentage, achievement, class, year, featured
    ("Suraj Doraya",     "94%",   "Tehsil Topper", "Class 10th", "2025-26", 1),
    ("Suraj Kumar",      "96%",   "",              "Class 10th", "2025-26", 0),
    ("Pihoo Borasiya",   "90.8%", "",              "Class 10th", "2025-26", 0),
    ("Archana Bairagi",  "86.6%", "",              "Class 10th", "2025-26", 0),
    ("Vanshika Panchal", "80.4%", "",              "Class 10th", "2025-26", 0),
    ("Dilisha Khan",     "78%",   "",              "Class 10th", "2025-26", 0),
    ("Kanishka Patidar", "69.8%", "",              "Class 10th", "2025-26", 0),
]

SEED_SERVICES = [
    ("Admission Open", "6th to 12th - All Subjects",
     "We have been providing coaching services since 2023 for every subject from class 6th to 12th.",
     "Upto 12th - Science, Humanities and Commerce\n"
     "Class 10th Special Batch\n"
     "Class 12th Special Batch\n"
     "JNVST Class 5th, 8th and 10th Special Batch",
     "Get a Quote", "/contact", 1),
    ("Foundation Batch", "Class 6th to 8th",
     "Concept-first teaching that builds a strong base in Maths, Science, English and Social Science.",
     "Weekly concept tests\nDaily doubt clearing\nHomework checking\nRegular parent updates",
     "Enquire Now", "/contact", 2),
    ("Board Exam Batch", "Class 10th and 12th",
     "Focused board preparation with previous-year papers, revision plans and full-length mock tests.",
     "Chapter-wise practice sheets\nMonthly full syllabus tests\nAnswer writing practice\n"
     "Personal performance tracking",
     "Enquire Now", "/contact", 3),
]

SEED_FACULTY = [
    ("Jitendra Kumar Verma", "Director",
     "BSc\nMSc Zoology\nBEd\nMA English",
     "Leads JK Classes Barnagar with a focus on strong fundamentals and disciplined preparation.", 1),
    ("Ajay Kumar Sen", "Co-Director",
     "BA\nMA English\nBEd\nMA Geography",
     "Guides the humanities and language faculty and mentors students through board preparation.", 2),
]

SEED_EVENTS = [
    ("New Batch Starting - Class 10th and 12th",
     "Fresh board-focused batches begin this month. Limited seats, admission on a "
     "first-come first-served basis.",
     "JK Classes Barnagar", "upcoming", "Book a Seat", "/contact"),
    ("Annual Result Felicitation Ceremony",
     "Our 2025-26 toppers were felicitated in the presence of their parents and our faculty members.",
     "JK Classes Barnagar", "completed", "", ""),
]

SEED_GALLERY = [
    ("Classroom session", "Classes"),
    ("Doubt clearing hour", "Classes"),
    ("Students at work", "Students"),
    ("Our coaching centre", "Campus"),
    ("Board practice test", "Classes"),
    ("Celebration day", "Events"),
    ("Group study", "Students"),
    ("Result day", "Results"),
]

GALLERY_CATEGORIES = ["Classes", "Events", "Students", "Results", "Campus", "Other"]


def init_db(app):
    """Create tables if missing and seed first-run content."""
    fresh = not os.path.exists(DB_PATH)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA)

    # Default admin account
    if con.execute("SELECT COUNT(*) FROM admins").fetchone()[0] == 0:
        con.execute(
            "INSERT INTO admins (username, password_hash) VALUES (?, ?)",
            (app.config["ADMIN_USERNAME"], generate_password_hash(app.config["ADMIN_PASSWORD"])),
        )

    # Settings: add any key that does not exist yet (safe on every restart)
    for key, value in DEFAULT_SETTINGS.items():
        con.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, value))

    if fresh:
        con.executemany(
            "INSERT INTO results (name, percentage, achievement, class_name, year, featured,"
            " sort_order) VALUES (?, ?, ?, ?, ?, ?, ?)",
            [(r[0], r[1], r[2], r[3], r[4], r[5], i) for i, r in enumerate(SEED_RESULTS)],
        )
        con.executemany(
            "INSERT INTO services (title, subtitle, description, points, button_text, button_link,"
            " sort_order) VALUES (?, ?, ?, ?, ?, ?, ?)",
            SEED_SERVICES,
        )
        con.executemany(
            "INSERT INTO faculty (name, role, qualifications, bio, sort_order)"
            " VALUES (?, ?, ?, ?, ?)",
            SEED_FACULTY,
        )
        today = date.today().isoformat()
        con.executemany(
            "INSERT INTO events (title, description, location, status, button_text, button_link,"
            " event_date) VALUES (?, ?, ?, ?, ?, ?, ?)",
            [(e[0], e[1], e[2], e[3], e[4], e[5], today) for e in SEED_EVENTS],
        )
        con.executemany(
            "INSERT INTO gallery (title, category, photo, sort_order) VALUES (?, ?, ?, ?)",
            [(g[0], g[1], "", i) for i, g in enumerate(SEED_GALLERY)],
        )

    con.commit()
    con.close()


def get_settings():
    """All settings as a plain dict, ready to drop into templates."""
    return {row["key"]: row["value"] for row in query("SELECT key, value FROM settings")}


def set_setting(key, value):
    execute(
        "INSERT INTO settings (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value or ""),
    )
