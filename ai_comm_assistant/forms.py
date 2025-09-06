"""Web forms used throughout the application."""

from flask_wtf import FlaskForm
from wtforms import (StringField, PasswordField, SubmitField, BooleanField,
                     TextAreaField, SelectField)
from wtforms.fields import EmailField
from wtforms.validators import DataRequired, Email, EqualTo, Length


class RegisterForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')


class LoginForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')


class DraftForm(FlaskForm):
    reply_text = TextAreaField('Reply', validators=[DataRequired()])
    tone = SelectField('Tone', choices=[('empathetic', 'Empathetic'),
                                        ('formal', 'Formal'),
                                        ('concise', 'Concise'),
                                        ('cheerful', 'Cheerful')], default='empathetic')
    language = SelectField('Language', choices=[('en', 'English'), ('hi', 'Hindi')], default='en')
    submit = SubmitField('Send')


class SettingsForm(FlaskForm):
    imap_host = StringField('IMAP Host', validators=[DataRequired()])
    imap_port = StringField('IMAP Port', validators=[DataRequired()])
    imap_user = StringField('IMAP Username', validators=[DataRequired()])
    imap_password = PasswordField('IMAP Password', validators=[DataRequired()])
    submit = SubmitField('Save')