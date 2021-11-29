from flask import flash, redirect, render_template, url_for, request, session
from flask_login import login_required, login_user, logout_user, current_user

from .. import log, app
from . import auth
from .forms import LoginForm
from ..models import User

@auth.route('/', methods=['GET', 'POST'])
def login():
    if 'api-key' in request.values:
        if request.values['api-key'] == app.config['API_KEY']:
            user = User.query.filter_by(username='admin').first()
            login_user(user)
            log.info('User used api-key')
            if 'redirect_url' in request.args:
                return redirect(request.args['redirect_url'])
            return redirect(url_for('overview.show'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user)
            log.info('User logged in')
            if 'redirect_url' in request.args:
                return redirect(request.args['redirect_url'])
            return redirect(url_for('overview.show'))
        else:
            flash('Ongeldige gebruikersnaam of paswoord')
    return render_template('auth/login.html', form=form, title='Login')

@auth.route('/logout')
@login_required
def logout():
    log.info('User logged out')
    logout_user()
    flash('U bent uitgelogd')
    return redirect(url_for('auth.login'))

