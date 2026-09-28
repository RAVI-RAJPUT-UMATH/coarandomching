"""
Image upload handling.

Every uploaded picture is checked (type + size), given a unique name and
stored in the `uploads/` folder. Only the file name goes into the database.
If Pillow is installed the image is also resized down so pages stay fast;
if it is not installed everything still works, the file is just saved as-is.
"""

import os
import secrets

from flask import current_app
from werkzeug.utils import secure_filename

try:
    from PIL import Image
    HAS_PILLOW = True
except ImportError:                     # Pillow is optional
    HAS_PILLOW = False

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "gif"}
MAX_WIDTH = 1600                        # uploaded photos are shrunk to this width
MAX_BYTES = 8 * 1024 * 1024             # 8 MB


def _extension(filename):
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def is_allowed(filename):
    return _extension(filename) in ALLOWED_EXTENSIONS


def save_upload(file_storage):
    """
    Save one uploaded file and return its stored file name.
    Returns "" when nothing was chosen or the file is not a valid image.
    """
    if not file_storage or not file_storage.filename:
        return ""

    if not is_allowed(file_storage.filename):
        return ""

    # Size check without loading the whole file into memory.
    file_storage.stream.seek(0, os.SEEK_END)
    size = file_storage.stream.tell()
    file_storage.stream.seek(0)
    if size == 0 or size > MAX_BYTES:
        return ""

    ext = _extension(file_storage.filename)
    safe_stem = secure_filename(file_storage.filename.rsplit(".", 1)[0])[:40] or "photo"
    filename = f"{safe_stem}-{secrets.token_hex(6)}.{ext}"
    path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)

    file_storage.save(path)
    _optimise(path, ext)
    return filename


def _optimise(path, ext):
    """Shrink very large photos so the website loads quickly on mobile data."""
    if not HAS_PILLOW or ext == "gif":
        return
    try:
        with Image.open(path) as img:
            if img.width <= MAX_WIDTH:
                return
            ratio = MAX_WIDTH / float(img.width)
            resized = img.resize((MAX_WIDTH, int(img.height * ratio)), Image.LANCZOS)
            if ext in ("jpg", "jpeg"):
                resized = resized.convert("RGB")
                resized.save(path, quality=85, optimize=True)
            else:
                resized.save(path, optimize=True)
    except Exception:
        # A picture we cannot process is still perfectly usable as uploaded.
        pass


def delete_upload(filename):
    """Remove an uploaded file from disk. Silently ignores anything missing."""
    if not filename:
        return
    path = os.path.join(current_app.config["UPLOAD_FOLDER"], os.path.basename(filename))
    try:
        if os.path.isfile(path):
            os.remove(path)
    except OSError:
        pass
