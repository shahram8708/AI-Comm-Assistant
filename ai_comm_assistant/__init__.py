"""Application factory and central glue for the AI communication assistant."""

import logging
import os

from flask import Flask
from .config import Config
from .extensions import db, bcrypt, login_manager, csrf


def create_app() -> Flask:
    """Create and configure the Flask application.

    This factory pattern allows for greater flexibility during testing and
    deployment.  Configuration is loaded from environment variables via the
    ``Config`` class.  Extensions are initialised and blueprints are
    registered.  The database schema is created on first run and seeded
    with initial data.
    """
    app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
                static_folder=os.path.join(os.path.dirname(__file__), 'static'))
    app.config.from_object(Config)

    # Initialise extensions
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id: str):
        from .models import User
        return User.query.get(int(user_id)) if user_id else None

    # Register blueprints
    from .routes.auth import auth_bp
    from .routes.main import main_bp
    from .routes.health import health_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(health_bp)

    # Create tables and seed initial data
    with app.app_context():
        db.create_all()
        try:
            from .seeds import seed_initial_data
            seed_initial_data()
        except Exception as e:
            app.logger.error(f"Error seeding initial data: {e}")

    # Configure logging
    logging.basicConfig(level=logging.INFO)
    return app