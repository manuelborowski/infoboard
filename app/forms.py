# -*- coding: utf-8 -*-
#app/forms.py

from flask_wtf import FlaskForm
from wtforms import SelectField
from . import db

class NonValidatingSelectFields(SelectField):
    def pre_validate(self, form):
        pass