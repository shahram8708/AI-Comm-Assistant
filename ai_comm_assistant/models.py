"""Database models for the AI communication assistant."""

from __future__ import annotations

import datetime as dt
from typing import Optional, List

from flask_login import UserMixin
from sqlalchemy.dialects.postgresql import JSON, BYTEA

from .extensions import db


class User(db.Model, UserMixin):
    """A registered agent or administrator.

    Roles: 'user' – an agent handling emails; 'admin' – privileged user.
    """
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(50), default='user')
    is_verified = db.Column(db.Boolean, default=False)
    locale = db.Column(db.String(10), default='en')
    created_at = db.Column(db.DateTime, default=dt.datetime.utcnow)

    threads = db.relationship('Thread', backref='owner', lazy=True)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User {self.email}>"


class KBEntry(db.Model):
    """A knowledge base entry used for retrieval‑augmented generation."""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    embedding = db.Column(BYTEA)  # store pickled embedding bytes
    created_at = db.Column(db.DateTime, default=dt.datetime.utcnow)


class Thread(db.Model):
    """An email thread containing multiple messages and a generated draft."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    thread_id = db.Column(db.String(255), nullable=False)  # identifier from mail server
    subject = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=dt.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=dt.datetime.utcnow, onupdate=dt.datetime.utcnow)
    sentiment = db.Column(db.String(50), default='neutral')
    urgency = db.Column(db.Boolean, default=False)
    priority_score = db.Column(db.Integer, default=0)
    resolved = db.Column(db.Boolean, default=False)

    emails = db.relationship('Email', backref='thread', cascade='all,delete', lazy=True)
    draft = db.relationship('Draft', backref='thread', uselist=False, cascade='all,delete', lazy=True)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Thread {self.thread_id} {self.subject}>"


class Email(db.Model):
    """An individual email within a thread."""
    id = db.Column(db.Integer, primary_key=True)
    thread_id = db.Column(db.Integer, db.ForeignKey('thread.id'), nullable=False)
    message_id = db.Column(db.String(255), nullable=True)
    sender = db.Column(db.String(255), nullable=False)
    recipients = db.Column(db.String(1024), nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    body = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=dt.datetime.utcnow)
    # Extracted info fields
    contact_details = db.Column(db.String(1024))
    keywords = db.Column(db.String(1024))
    sentiment = db.Column(db.String(50), default='neutral')
    urgency = db.Column(db.Boolean, default=False)
    attachments = db.relationship('Attachment', backref='email', cascade='all,delete', lazy=True)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Email from {self.sender} subject {self.subject}>"


class Attachment(db.Model):
    """A file attached to an email."""
    id = db.Column(db.Integer, primary_key=True)
    email_id = db.Column(db.Integer, db.ForeignKey('email.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    content_type = db.Column(db.String(255))
    path = db.Column(db.String(1024), nullable=False)
    extracted_text = db.Column(db.Text)


class Draft(db.Model):
    """A generated reply associated with a thread."""
    id = db.Column(db.Integer, primary_key=True)
    thread_id = db.Column(db.Integer, db.ForeignKey('thread.id'), nullable=False)
    reply_text = db.Column(db.Text, nullable=False)
    justification = db.Column(db.Text)
    confidence_score = db.Column(db.Float, default=0.0)
    tone = db.Column(db.String(50), default='empathetic')
    sentiment = db.Column(db.String(50), default='neutral')
    coach_score = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=dt.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=dt.datetime.utcnow, onupdate=dt.datetime.utcnow)
    is_sent = db.Column(db.Boolean, default=False)
    feedback = db.relationship('Feedback', backref='draft', cascade='all,delete', uselist=False)


class Feedback(db.Model):
    """Feedback provided by an agent after editing an AI draft."""
    id = db.Column(db.Integer, primary_key=True)
    draft_id = db.Column(db.Integer, db.ForeignKey('draft.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    edited_reply = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=dt.datetime.utcnow)

    user = db.relationship('User')


class Notification(db.Model):
    """Notification sent for unresolved urgent emails."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    email_id = db.Column(db.Integer, db.ForeignKey('email.id'))
    message = db.Column(db.String(1024), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # slack or email
    sent_at = db.Column(db.DateTime, default=dt.datetime.utcnow)

    user = db.relationship('User')
    email = db.relationship('Email')