"""Unit tests for database models."""

from ai_comm_assistant.extensions import db, bcrypt
from ai_comm_assistant.models import User, Thread, Email


def test_user_creation(app):
    with app.app_context():
        user = User.query.filter_by(email='agent@example.com').first()
        assert user is not None
        assert user.role == 'user'
        assert bcrypt.check_password_hash(user.password_hash, 'Password123!')


def test_thread_and_email_relationship(app):
    with app.app_context():
        user = User.query.filter_by(email='agent@example.com').first()
        thread = Thread(user_id=user.id, thread_id='test-thread', subject='Test Subject')
        email = Email(thread=thread, sender='customer@test.com', recipients='agent@example.com', subject='Test Subject', body='Hello')
        db.session.add(thread)
        db.session.add(email)
        db.session.commit()
        assert thread.emails[0] == email
        assert email.thread == thread