"""
WSGI config for DWLR project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DWLR.settings')

application = get_wsgi_application()
app = application

# Serverless SQLite on Vercel has no persistent disk. Apply schema on cold start
# so signup/login work until a hosted DATABASE_URL is attached.
if os.getenv("VERCEL") == "1" and not os.getenv("DATABASE_URL"):
    from django.core.management import call_command

    call_command("migrate", interactive=False, run_syncdb=True)
