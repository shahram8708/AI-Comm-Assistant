"""Configuration definitions for the application.

Configuration values are pulled from environment variables with sensible
defaults for development.  Do not commit sensitive secrets to version control;
use a `.env` file or external secret management.
"""

import os
from datetime import timedelta


class Config:
    # Core settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'change_me')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Celery / Redis configuration
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_RESULT_SERIALIZER = 'json'
    CELERY_ACCEPT_CONTENT = ['json']
    CELERY_BEAT_SCHEDULE = {}

    # Google Gemini API
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

    # Email settings
    MAIL_IMAP_HOST = os.getenv('MAIL_IMAP_HOST', '')
    MAIL_IMAP_PORT = int(os.getenv('MAIL_IMAP_PORT', '993'))
    MAIL_IMAP_USER = os.getenv('MAIL_IMAP_USER', '')
    MAIL_IMAP_PASSWORD = os.getenv('MAIL_IMAP_PASSWORD', '')
    MAIL_CLIENT_ID = os.getenv('MAIL_CLIENT_ID', '')
    MAIL_CLIENT_SECRET = os.getenv('MAIL_CLIENT_SECRET', '')
    MAIL_REFRESH_TOKEN = os.getenv('MAIL_REFRESH_TOKEN', '')
    MAIL_MAILBOX = os.getenv('MAIL_MAILBOX', 'INBOX')

    SMTP_HOST = os.getenv('SMTP_HOST', '')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
    SMTP_USERNAME = os.getenv('SMTP_USERNAME', '')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')

    # Slack notifications
    SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL', '')

    OFFLINE_MODE = os.getenv('OFFLINE_MODE', 'false').lower() == 'true'
    PRIORITY_TIMEOUT_MINUTES = int(os.getenv('PRIORITY_TIMEOUT_MINUTES', '30'))

    # Internationalisation
    DEFAULT_LANGUAGE = os.getenv('DEFAULT_LANGUAGE', 'en')
    SUPPORTED_LANGUAGES = [lang.strip() for lang in os.getenv('SUPPORTED_LANGUAGES', 'en,hi').split(',')]

    # Misc
    SESSION_COOKIE_NAME = 'ai_comm_session'
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)