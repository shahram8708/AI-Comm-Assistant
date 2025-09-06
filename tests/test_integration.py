"""Integration tests for the Flask app."""

from ai_comm_assistant.extensions import db
from ai_comm_assistant.models import User, Thread, Email, Draft


def login(client, email: str, password: str):
    return client.post('/auth/login', data={'email': email, 'password': password}, follow_redirects=True)


def test_login_and_inbox(client):
    # Login using seeded user
    rv = login(client, 'agent@example.com', 'Password123!')
    assert b'Logged in successfully' in rv.data or rv.status_code == 200
    # Access inbox
    resp = client.get('/inbox')
    assert resp.status_code == 200


def test_thread_reply_flow(client, app):
    # Login
    login(client, 'agent@example.com', 'Password123!')
    with app.app_context():
        user = User.query.filter_by(email='agent@example.com').first()
        # Create a thread and draft manually
        thread = Thread(user_id=user.id, thread_id='test', subject='Integration Test')
        email_record = Email(thread=thread, sender='customer@example.com', recipients=user.email,
                             subject='Integration Test', body='I need help')
        draft = Draft(thread=thread, reply_text='We will help you.', justification='Test', confidence_score=0.9)
        db.session.add_all([thread, email_record, draft])
        db.session.commit()
        thread_id = thread.id
    # Access thread
    resp = client.get(f'/thread/{thread_id}')
    assert resp.status_code == 200
    # Send reply via form
    resp = client.post(f'/thread/{thread_id}', data={'reply_text': 'Updated reply', 'tone': 'formal', 'language': 'en'}, follow_redirects=True)
    assert b'Reply sent' in resp.data
    with app.app_context():
        draft = Draft.query.filter_by(thread_id=thread_id).first()
        assert draft.is_sent is True