"""Database seeding utilities."""

from __future__ import annotations

from .extensions import db, bcrypt
from .models import User, KBEntry


def seed_initial_data() -> None:
    """Seed the database with initial users and KB entries if empty."""
    # Create default users
    if User.query.first() is None:
        admin = User(email='admin@example.com', password_hash=bcrypt.generate_password_hash('Password123!').decode('utf-8'), role='admin', is_verified=True)
        agent = User(email='agent@example.com', password_hash=bcrypt.generate_password_hash('Password123!').decode('utf-8'), role='user', is_verified=True)
        db.session.add(admin)
        db.session.add(agent)
        db.session.commit()
    # Create basic KB entries
    if KBEntry.query.first() is None:
        entries = [
            KBEntry(title='Shipping policy', content='Our standard shipping time is 3–5 business days. You can track your order using the tracking number provided in your confirmation email.'),
            KBEntry(title='Return policy', content='Items can be returned within 30 days of receipt. Please include the original packaging and proof of purchase.'),
            KBEntry(title='Technical support', content='For technical issues with our products, contact our support team at support@example.com with a detailed description of the problem.'),
        ]
        db.session.bulk_save_objects(entries)
        db.session.commit()