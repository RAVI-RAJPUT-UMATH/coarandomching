"""
Image upload handling.

- Local development: saves images in uploads/
- Vercel: saves images permanently in Vercel Blob
"""

import os
import secrets
import tempfile

from flask import current_app
from werkzeug.utils import secure_filename

try:
    from PIL import Image
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False


ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "gif"}

# Must stay below Vercel's 4.5 MB Function request limit.
MAX_BYTES = 3 * 1024 * 1024

MAX_WIDTH = 1600


def _extension(filename):
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def is_allowed(filename):
    return _extension(filename) in ALLOWED_EXTENSIONS


def save_upload(file_storage):
    """
    Save an uploaded image.

    Local:
        Returns the local filename.

    Vercel:
        Uploads to Vercel Blob and returns the public Blob URL.
    """

    if not file_storage or not file_storage.filename:
        return ""

    original_filename = file_storage.filename

    if not is_allowed(original_filename):
        return ""

    # Check file size.
    file_storage.stream.seek(0, os.SEEK_END)
    size = file_storage.stream.tell()
    file_storage.stream.seek(0)

    if size == 0 or size > MAX_BYTES:
        return ""

    ext = _extension(original_filename)

    safe_stem = (
        secure_filename(
            original_filename.rsplit(".", 1)[0]
        )[:40]
        or "photo"
    )

    filename = f"{safe_stem}-{secrets.token_hex(6)}.{ext}"

    # =========================================================
    # VERCEL
    # =========================================================

    if os.environ.get("VERCEL"):
        return _upload_to_vercel_blob(
            file_storage,
            filename
        )

    # =========================================================
    # LOCAL
    # =========================================================

    upload_folder = current_app.config["UPLOAD_FOLDER"]

    os.makedirs(upload_folder, exist_ok=True)

    path = os.path.join(upload_folder, filename)

    file_storage.save(path)

    _optimise(path, ext)

    return filename


def _upload_to_vercel_blob(file_storage, filename):
    """
    Upload a file to Vercel Blob.

    Returns the permanent public Blob URL.
    """

    temp_path = os.path.join(
        tempfile.gettempdir(),
        filename
    )

    try:
        # Save uploaded file temporarily.
        file_storage.save(temp_path)

        # Current Vercel Python SDK.
        from vercel import blob

        uploaded_file = blob.upload_file(
            local_path=temp_path,
            path=f"gallery/{filename}",
            access="public"
        )

        return uploaded_file.url

    finally:
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except OSError:
            pass


def _optimise(path, ext):
    """
    Shrink very large photos.
    """

    if not HAS_PILLOW or ext == "gif":
        return

    try:
        with Image.open(path) as img:

            if img.width <= MAX_WIDTH:
                return

            ratio = MAX_WIDTH / float(img.width)

            resized = img.resize(
                (
                    MAX_WIDTH,
                    int(img.height * ratio)
                ),
                Image.LANCZOS
            )

            if ext in ("jpg", "jpeg"):
                resized = resized.convert("RGB")

                resized.save(
                    path,
                    quality=85,
                    optimize=True
                )

            else:
                resized.save(
                    path,
                    optimize=True
                )

    except Exception:
        # If optimization fails, keep the original image.
        pass


def delete_upload(filename):
    """
    Delete a local uploaded file.

    Blob URLs are left untouched for now.
    """

    if not filename:
        return

    # Blob URL — don't try to delete it as a local file.
    if filename.startswith("http://") or filename.startswith("https://"):
        return

    path = os.path.join(
        current_app.config["UPLOAD_FOLDER"],
        os.path.basename(filename)
    )

    try:
        if os.path.isfile(path):
            os.remove(path)

    except OSError:
        pass