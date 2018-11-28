# -*- coding: utf-8 -*-
#app/forms.py

from flask_wtf import FlaskForm
from wtforms import SelectField
from models import Registration, Series
from . import db


class GenderFilter(FlaskForm):
    def __init__(self, *args, **kwargs):
        super(GenderFilter, self).__init__(*args, **kwargs)
        ql = [r.gender for r in  db.session.query(Registration.gender).distinct()]
        ql.insert(0, '')
        self.gender.choices=zip(ql, ql)

    gender = SelectField('')

class SeriesFilter(FlaskForm):
    def __init__(self, *args, **kwargs):
        super(SeriesFilter, self).__init__(*args, **kwargs)
        ql = [s.name for s in  db.session.query(Series.name).distinct()]
        ql.insert(0, '')
        self.series.choices=zip(ql, ql)

    series = SelectField('')

class NonValidatingSelectFields(SelectField):
    def pre_validate(self, form):
        pass