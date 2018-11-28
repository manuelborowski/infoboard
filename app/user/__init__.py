# -*- coding: utf-8 -*-
# app/auth/__init__.py

from flask import Blueprint
from flask_login import login_required, current_user
from ..models import User

user = Blueprint('user', __name__)

from . import views
