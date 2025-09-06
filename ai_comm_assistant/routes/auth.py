"""Authentication routes blueprint."""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user

from ..extensions import db, bcrypt
from ..models import User
from ..forms import RegisterForm, LoginForm


auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = RegisterForm()
    if form.validate_on_submit():
        existing = User.query.filter_by(email=form.email.data.lower()).first()
        if existing:
            flash('An account with that email already exists.', 'danger')
            return redirect(url_for('auth.register'))
        hashed = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(email=form.email.data.lower(), password_hash=hashed)
        db.session.add(user)
        db.session.commit()
        # Simulate email verification
        verification_link = url_for('auth.verify_email', user_id=user.id, _external=True)
        print(f"[Verification] Send this link to the user: {verification_link}")
        flash('Account created! Check console for verification link.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('register.html', form=form)


@auth_bp.route('/verify/<int:user_id>')
def verify_email(user_id: int):
    user = User.query.get_or_404(user_id)
    user.is_verified = True
    db.session.commit()
    flash('Your email has been verified. You can now log in.', 'success')
    return redirect(url_for('auth.login'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user and bcrypt.check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember.data)
            flash('Logged in successfully.', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.dashboard'))
        flash('Invalid credentials. Please try again.', 'danger')
    return render_template('login.html', form=form)


@auth_bp.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))