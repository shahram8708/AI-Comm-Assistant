import os
import pytest

from ai_comm_assistant import create_app
from ai_comm_assistant.extensions import db


@pytest.fixture(scope='session')
def app():
    # Configure a test app with an in‑memory SQLite database
    os.environ['GEMINI_API_KEY'] = 'test'  # dummy key
    app = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'CELERY_TASK_ALWAYS_EAGER': True,
    })
    with app.app_context():
        db.create_all()
        from ai_comm_assistant.seeds import seed_initial_data
        seed_initial_data()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()