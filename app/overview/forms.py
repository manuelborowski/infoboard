# -*- coding: utf-8 -*-
#app/auth/forms.py

from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, BooleanField, ValidationError, IntegerField
from wtforms.validators import DataRequired, Email, EqualTo
from wtforms.widgets import HiddenInput

from ..models import Switches


class EditForm(FlaskForm):
    name = StringField('Naam')
    ip = StringField('IP')
    location = StringField('Locatie')
    type = StringField('Type')
    id = IntegerField(widget=HiddenInput())

class AddForm(EditForm):
    pass