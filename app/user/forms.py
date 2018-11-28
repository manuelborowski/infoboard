# -*- coding: utf-8 -*-
#app/auth/forms.py

from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, BooleanField, ValidationError, IntegerField
from wtforms.validators import DataRequired, Email, EqualTo
from wtforms.widgets import HiddenInput

from ..models import User


class EditForm(FlaskForm):
    """
    Edit an existing user
    """

    first_name = StringField('First name')
    last_name = StringField('Last name')
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email')
    is_admin = BooleanField('Is admin')
    id = IntegerField(widget=HiddenInput())

class AddForm(EditForm):
    """
    Add a user
    """
    password = PasswordField('Password', validators=[DataRequired(), EqualTo('confirm_password')])
    confirm_password = PasswordField('Confirm Password')
    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username is already in use')



class ViewForm(FlaskForm):
    """
    View an existing user
    """

    first_name = StringField('First name', render_kw={'readonly':''})
    last_name = StringField('Last name', render_kw={'readonly':''})
    username = StringField('Username', render_kw={'readonly':''})
    email = StringField('Email', render_kw={'readonly':''})
    is_admin = BooleanField('Is admin', render_kw={'readonly':''})
    id = IntegerField(widget=HiddenInput())

class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('Old password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), EqualTo('confirm_new_password')])
    confirm_new_password = PasswordField('Confirm new password')
