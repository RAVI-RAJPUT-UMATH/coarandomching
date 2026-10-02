"""
WSGI entry point for production hosting (PythonAnywhere, waitress, gunicorn).

PythonAnywhere
--------------
In the Web tab, open the "WSGI configuration file" link and replace its whole
contents with:

    import sys
    path = "/home/YOURUSERNAME/jk"       # <- your project folder
    if path not in sys.path:
        sys.path.insert(0, path)

    from wsgi import application

Set SECRET_KEY in the Web tab's "Environment variables" section first.

Local check
-----------
    pip install waitress
    waitress-serve --port=8000 wsgi:application
"""

import os
import sys

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app import app as application          # noqa: E402

# Never serve the debug toolbar / interactive debugger in production.
application.config["DEBUG"] = False

if not os.environ.get("SECRET_KEY"):
    print(
        "WARNING: SECRET_KEY is not set, so the built-in development key is in "
        "use. Anyone who has seen the source can forge an admin session. Set "
        "SECRET_KEY as an environment variable before going live.",
        file=sys.stderr,
    )
