# -*- coding: utf-8 -*-
# app/auth/views.py

from flask import flash, redirect, render_template, url_for, request, session
from flask_login import login_required, login_user, logout_user, current_user

from .. import log
from . import auth
from forms import LoginForm
from ..models import User

@auth.route('/', methods=['GET', 'POST'])
def login():
    """
    Handle requests to the /login route
    Log an employee in through the login form
    """

    form = LoginForm()
    if form.validate_on_submit():
        # check whether user exists in the database and whether
        # the password entered matches the password in the database
        user = User.query.filter_by(username=form.username.data).first()
        if user is not None and user.verify_password(form.password.data):
            # log user in
            login_user(user)
            log.info('User logged in')

            # redirect to the appropriate page
            if 'redirect_url' in request.args:
                return redirect(request.args['redirect_url'])
            return redirect(url_for('registration.register'))
            # when login details are incorrect
        else:
            flash('Ongeldige gebruikersnaam of paswoord')

     # load login template
    return render_template('auth/login.html', form=form, title='Login')

@auth.route('/logout')
@login_required
def logout():
    """
    Handle requests to the /logout route
    Log a user out through the logout link
    """
    log.info('User logged out')
    logout_user()
    flash('U bent uitgelogd')

    # redirect to the login page
    return redirect(url_for('auth.login'))

