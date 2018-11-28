# -*- coding: utf-8 -*-
# app/models.py

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import db, login_manager, ms2m_s_ms
from sqlalchemy import UniqueConstraint
from sqlalchemy.sql import func

class User(UserMixin, db.Model):
    # Ensures table will be named in plural and not in singular
    # as is the name of the model
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(256))
    username = db.Column(db.String(256), index=True, unique=True)
    first_name = db.Column(db.String(256))
    last_name = db.Column(db.String(256))
    password_hash = db.Column(db.String(256))
    is_admin = db.Column(db.Boolean, default=False)
    settings = db.relationship('Settings', cascade='all, delete', backref='user', lazy='dynamic')

    @property
    def password(self):
        """
        Prevent pasword from being accessed
        """
        raise AttributeError('Paswoord kan je niet lezen.')

    @password.setter
    def password(self, password):
        """
        Set password to a hashed password
        """
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        """
        Check if hashed password matches actual password
        """
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return '<User: {}>'.format(self.username)

    def log(self):
        return '<User: {}/{}>'.format(self.id, self.username)

    def ret_dict(self):
        return {'id':self.id, 'email':self.email, 'username':self.username, 'first_name':self.first_name, 'last_name':self.last_name,
                'is_admin': self.is_admin}

# Set up user_loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Settings(db.Model):
    __tablename__ = 'settings'

    class SETTING_TYPE:
        E_INT = 'INT'
        E_STRING = 'STRING'
        E_FLOAT = 'FLOAT'
        E_BOOL = 'BOOL'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256))
    value = db.Column(db.String(256))
    type = db.Column(db.String(256))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))

    UniqueConstraint('name', 'user_id')

    def log(self):
        return '<Setting: {}/{}/{}/{}>'.format(self.id, self.name, self.value, self.type)


class Series(db.Model):
    __tablename__ = 'series'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256))
    sequence = db.Column(db.Integer)
    starttime = db.Column(db.DateTime())
    running = db.Column(db.Boolean, default=False)
    registration = db.relationship('Registration', cascade='all, delete', backref='series', lazy='dynamic')

    def __repr__(self):
        return u'<Series>: {}/{}/{}/{}'.format(self.id, self.name, self.sequence, self.starttime)

    def ret_dict(self):
        return {'id': self.id, 'name': self.name, 'sequence': self.sequence, 'starttime': self.starttime}


class Registration(db.Model):
    __tablename__ = 'registrations'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(256))
    last_name = db.Column(db.String(256))
    gender = db.Column(db.String(256))
    classgroup = db.Column(db.String(256))
    studentcode = db.Column(db.String(256), unique=True)
    rfidcode = db.Column(db.String(256), unique=True)
    rfidcode2 = db.Column(db.String(256), unique=True)
    time_ran = db.Column(db.Integer)
    time_registered = db.Column(db.DateTime())
    series_id = db.Column(db.Integer, db.ForeignKey('series.id', ondelete='CASCADE'))

    def __repr__(self):
        return u'<Registration: {}/{}/{}/{}/{}/{}/{}/{}/{}'.format(self.id, self.first_name, self.last_name,
                                                                   self.gender, self.classgroup,
                                                         self.studentcode, self.rfidcode, self.rfidcode2, self.time_ran)

    def ret_dict(self):
        return {'id':self.id, 'first_name':self.first_name, 'last_name': self.last_name, 'gender': self.gender,
                'classgroup': self.classgroup,
                'full_name': u'{} {}'.format(self.first_name, self.last_name), 'rfidcode': self.rfidcode, 'rfidcode2': self.rfidcode2,
                'studentcode': self.studentcode, 'time_ran': ms2m_s_ms(self.time_ran), 'series': self.series.ret_dict()}


