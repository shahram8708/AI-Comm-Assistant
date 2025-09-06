"""Background tasks powered by Celery."""

from __future__ import annotations

import os
import datetime as dt
import json
from typing import List

from celery import Celery
from flask import Flask
import requests

from .config import Config
from .extensions import db
from .models import User, Thread, Email, Attachment, Draft, Feedback, Notification
from .services import email_utils
from .services.gemini_adapter import GeminiAdapter
from .services.sentiment import detect_sentiment_and_urgency
from .services.rag import RAGService
from .utils import calculate_priority, calculate_trust


def make_celery(app: Flask) -> Celery:
    """Create a Celery object and tie it to the Flask app's context."""
    celery = Celery(
        app.import_name,
        broker=app.config['CELERY_BROKER_URL'],
        backend=app.config['CELERY_RESULT_BACKEND'],
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery


def create_celery_app() -> Celery:
    """Factory to create Celery without requiring an app context on import."""
    from . import create_app
    flask_app = create_app()
    return make_celery(flask_app)


# Initialise Celery with Flask application context
from . import create_app
flask_app = create_app()
celery = make_celery(flask_app)


@celery.task
def fetch_emails_task():
    """Periodic task to fetch new emails for all users."""
    users = User.query.all()
    total = 0
    for user in users:
        if user.role != 'user':
            continue
        processed = email_utils.fetch_and_store_emails(user.id)
        total += processed
    return total


@celery.task
def process_emails_task():
    """Process unprocessed emails: extract info, update threads, generate drafts."""
    from .config import Config as AppConfig
    offline = AppConfig.OFFLINE_MODE
    adapter = None if offline else GeminiAdapter()
    rag_service = None if offline else RAGService()
    # Find emails without sentiment (unprocessed)
    emails = Email.query.filter_by(sentiment='neutral').all()
    for email_record in emails:
        # Extract attachment text
        attachment_text = ''
        if not offline and adapter:
            for att in email_record.attachments:
                extracted = adapter.extract_text_from_file(att.path)
                att.extracted_text = extracted
                attachment_text += '\n' + extracted
        # Detect sentiment & urgency using heuristics on body + attachments
        combined_text = f"{email_record.body}\n{attachment_text}"
        sentiment, urgency = detect_sentiment_and_urgency(combined_text)
        email_record.sentiment = sentiment
        email_record.urgency = urgency
        # Update thread metadata
        thread = email_record.thread
        thread.sentiment = sentiment
        thread.urgency = urgency
        thread.priority_score = calculate_priority(sentiment, urgency, email_record.timestamp)
        # In offline mode skip reply generation
        if offline or adapter is None or rag_service is None:
            db.session.commit()
            continue
        # Build context from thread emails
        thread_text = '\n\n'.join([f"From: {e.sender}\nSubject: {e.subject}\n{e.body}" for e in thread.emails])
        # Retrieve KB context
        kb_snippets = rag_service.get_top_k(thread_text, k=3)
        kb_context = '\n---\n'.join(kb_snippets)
        # Generate draft
        tone = 'empathetic' if sentiment == 'negative' else 'formal'
        result = adapter.generate_reply(thread_text, kb_context, tone, sentiment, urgency)
        # Save draft
        draft = thread.draft or Draft(thread=thread)
        draft.reply_text = result['reply_text']
        draft.justification = result['justification']
        draft.confidence_score = result['confidence']
        draft.tone = tone
        draft.sentiment = sentiment
        # Compute trust
        draft.coach_score = int(calculate_trust(result['confidence']))
        db.session.add(draft)
        db.session.commit()
    return len(emails)


@celery.task
def send_notifications_task():
    """Notify when urgent threads remain unresolved beyond the timeout."""
    now = dt.datetime.utcnow()
    timeout = dt.timedelta(minutes=Config.PRIORITY_TIMEOUT_MINUTES)
    threads = Thread.query.filter_by(resolved=False, urgency=True).all()
    for thread in threads:
        # Check if last email is older than timeout
        last_email = max(thread.emails, key=lambda e: e.timestamp)
        if now - last_email.timestamp < timeout:
            continue
        # Compose message
        message = f"Urgent thread '{thread.subject}' has been pending for more than {Config.PRIORITY_TIMEOUT_MINUTES} minutes."
        # Slack notification
        if Config.SLACK_WEBHOOK_URL:
            try:
                requests.post(Config.SLACK_WEBHOOK_URL, json={'text': message}, timeout=5)
                notif = Notification(user_id=thread.user_id, email_id=last_email.id, message=message, type='slack')
                db.session.add(notif)
                db.session.commit()
            except Exception:
                pass
    return len(threads)