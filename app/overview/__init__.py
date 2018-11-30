# -*- coding: utf-8 -*-
# app/home/__init__.py

from flask import Blueprint

overview = Blueprint('overview', __name__)

from . import views