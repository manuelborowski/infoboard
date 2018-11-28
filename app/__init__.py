# -*- coding: utf-8 -*-

# app/__init__.py

# third-party imports
from flask import Flask, render_template, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from flask_bootstrap import Bootstrap
from flask_jsglue import JSGlue
from werkzeug.routing import IntegerConverter as OrigIntegerConvertor
import config, logging, logging.handlers, os, sys
import flask_excel as excel
import random

app = Flask(__name__, instance_relative_config=True)

#enable logging
LOG_HANDLE = 'RR'
log = logging.getLogger(LOG_HANDLE)

# local imports
from config import app_config

db = SQLAlchemy()
login_manager = LoginManager()

#The original werkzeug-url-converter cannot handle negative integers (e.g. asset/add/-1/1)
class IntegerConverter(OrigIntegerConvertor):
    regex = r'-?\d+'
    num_convert = int


def create_admin(db):
    from app.models import User
    admin = User(username='admin', password='admin', is_admin=True)
    db.session.add(admin)
    db.session.commit()

#support custom filtering while logging
class MyLogFilter(logging.Filter):
    def filter(self, record):
        record.username = current_user.username if current_user and current_user.is_active else 'NONE'
        return True

def ms2m_s_ms(value):
    if value:
        min = value/60000
        sec = int((value - min*60000)/1000)
        msec = value - min*60000 - sec*1000
        return('{}:{:02d},{}'.format(min, sec, msec))
    else:
        return None


def create_app(config_name):
    global app
    global log

    #set up logging
    LOG_FILENAME = os.path.join(sys.path[0], app_config[config_name].STATIC_PATH, 'log/rr-log.txt')
    try:
        log_level = getattr(logging, app_config[config_name].LOG_LEVEL)
    except:
        log_level = getattr(logging, 'INFO')
    log.setLevel(log_level)
    log.addFilter(MyLogFilter())
    log_handler = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=10 * 1024, backupCount=5)
    log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(username)s - %(message)s')
    log_handler.setFormatter(log_formatter)
    log.addHandler(log_handler)

    log.info('start RR')

    app.config.from_object(app_config[config_name])
    app.config.from_pyfile('config.py')

    app.jinja_env.filters['milliseconds_to_minutes_seconds'] = ms2m_s_ms

    Bootstrap(app)

    jsglue = JSGlue(app)
    db.app=app  # hack :-(
    db.init_app(app)
    excel.init_excel(app)

    app.url_map.converters['int'] = IntegerConverter

    random.seed()

    if not config.DB_TOOLS:
        login_manager.init_app(app)
        login_manager.login_message = 'Je moet aangemeld zijn om deze pagina te zien!'
        login_manager.login_view = 'auth.login'

        migrate = Migrate(app, db)

        from app import models

        #create_admin(db) # Only once

        #flask db migrate
        #flask db upgrade
        #uncheck when migrating database
        #return app

        from .auth import auth as auth_blueprint
        app.register_blueprint(auth_blueprint)

        from .settings import settings as settings_blueprint
        app.register_blueprint(settings_blueprint)

        from .user import user as user_blueprint
        app.register_blueprint(user_blueprint)

        from .registration import registration as registration_blueprint
        app.register_blueprint(registration_blueprint)

        @app.errorhandler(403)
        def forbidden(error):
            return render_template('errors/403.html', title='Forbidden'), 403

        @app.errorhandler(404)
        def page_not_found(error):
            return render_template('errors/404.html', title='Page Not Found'), 404

        @app.errorhandler(500)
        def internal_server_error(error):
            return render_template('errors/500.html', title='Server Error'), 500

        @app.route('/500')
        def error_500():
            abort(500)
    return app

