from ai_comm_assistant import create_app

# A WSGI entry point for gunicorn/uwsgi.  This module exposes the
# Flask application as `app` so that a WSGI server can discover it.
app = create_app()