"""
ASGI config for the project.
Used when deploying with an ASGI server, or if async features are added later.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_asgi_application()
