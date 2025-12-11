"""
WSGI config for flood_warning_system project.
It exposes the WSGI callable as a module-level variable named ``application``.
"""

import os
import sys

from django.core.wsgi import get_wsgi_application
from django.core.management import execute_from_command_line

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "flood_warning_system.settings")

application = get_wsgi_application()

try:
    from django.core.management import call_command
except Exception as e:
    print(f"Error initializing application: {e}")