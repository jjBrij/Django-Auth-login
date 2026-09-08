"""
WSGI config for the project.
Used when deploying with a traditional WSGI server (e.g. gunicorn).
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_wsgi_application()
