"""
Image upload handling for JK Classes Barnagar.

Uploaded images are validated, resized when possible, and stored
permanently in Vercel Blob when running on Vercel.

For local development, images are stored in the local uploads/ folder.
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

# Keep this below Vercel's 4.5 MB server request limit.
MAX_BYTES = 3 * 1024 * 1024

MAX_WIDTH = 1600


def _extension(filename):
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def is_allowed(filename):
    return _extension(filename) in ALLOWED_EXTENSIONS


def save_upload(file_storage):
    """
    Validate and save an uploaded image.

    On Vercel:
        Uploads the image to Vercel Blob and returns its public URL.

    Locally:
        Saves the image inside the local uploads/ folder and returns
        the local filename.
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
        secure_filename(original_filename.rsplit(".", 1)[0])[:40]
        or "photo"
    )

    filename = f"{safe_stem}-{secrets.token_hex(6)}.{ext}"

    # ---------------------------------------------------------
    # VERCEL
    # ---------------------------------------------------------
    if os.environ.get("VERCEL"):
        return _upload_to_vercel_blob(
            file_storage,
            filename,
            ext
        )

    # ---------------------------------------------------------
    # LOCAL DEVELOPMENT
    # ---------------------------------------------------------
    upload_folder = current_app.config["UPLOAD_FOLDER"]

    os.makedirs(upload_folder, exist_ok=True)

    path = os.path.join(upload_folder, filename)

    file_storage.save(path)

    _optimise(path, ext)

    return filename


def _upload_to_vercel_blob(file_storage, filename, ext):
    """
    Upload image to Vercel Blob and return the public URL.
    """

    # Save temporarily because the Python Blob SDK accepts bytes/file data.
    temp_path = os.path.join(
        tempfile.gettempdir(),
        filename
    )

    try:
        file_storage.save(temp_path)

        # Import only when running on Vercel.
        from vercel.blob import BlobClient

        with open(temp_path, "rb") as f:
            file_data = f.read()

        client = BlobClient()

        blob = client.put(
            f"gallery/{filename}",
            file_data,
            access="public",
            content_type=file_storage.mimetype or f"image/{ext}",
            add_random_suffix=False,
        )

        return blob.url

    finally:
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except OSError:
            pass


def _optimise(path, ext):
    """
    Shrink very large photos so the website loads quickly.
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
        # Keep original image if optimization fails.
        pass


def delete_upload(filename):
    """
    Delete an uploaded image.

    Local files are deleted from disk.

    Vercel Blob files are intentionally not deleted here yet because
    the database currently stores the returned Blob URL rather than
    a local filename.
    """

    if not filename:
        return

    # Vercel Blob URLs should not be treated as local files.
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