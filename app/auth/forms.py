# -*- coding: utf-8 -*-
#app/auth/forms.py

from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired

class LoginForm(FlaskForm):
    """
    For users who want to log in
    """
    username = StringField('Gebruikersnaam', validators=[DataRequired()], render_kw={'autofocus': 'true'})
    password = PasswordField('Paswoord', validators=[DataRequired()])
    submit_button = SubmitField('Login')
