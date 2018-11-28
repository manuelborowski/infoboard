# -*- coding: utf-8 -*-
# app/home/__init__.py

from flask import Blueprint

registration = Blueprint('registration', __name__)

from . import views