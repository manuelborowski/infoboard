# -*- coding: utf-8 -*-
# app/user/views.py

from flask import render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user

from .forms import AddForm, EditForm, ViewForm, ChangePasswordForm
from .. import db, log
from . import user
from ..models import User

from ..base import build_filter, get_ajax_table
from ..tables_config import  tables_configuration
from ..floating_menu import user_menu_config, admin_menu_config

#This route is called by an ajax call on the assets-page to populate the table.
@user.route('/user/data', methods=['GET', 'POST'])
@login_required
def source_data():
    return get_ajax_table(tables_configuration['user'])

#ashow a list of purchases
@user.route('/user', methods=['GET', 'POST'])
@login_required
def users():
    #The following line is required only to build the filter-fields on the page.
    _filter, _filter_form, a,b, c = build_filter(tables_configuration['user'])
    config = tables_configuration['user']
    #floating menu depends if current user is admin or not
    if current_user.is_admin:
        config['floating_menu'] = admin_menu_config
    else:
        config['floating_menu'] = user_menu_config

    return render_template('base_multiple_items.html',
                           title='users',
                           filter=_filter, filter_form=_filter_form,
                           config=config)


#add a new user
@user.route('/user/add/<int:id>', methods=['GET', 'POST'])
@user.route('/user/add', methods=['GET', 'POST'])
@login_required
def add(id=-1):
    if id > -1:
        user = User.query.get_or_404(int(id))
        form = AddForm(obj=user)
    else:
        form = AddForm()
    del form.id # is not required here and makes validate_on_submit fail...
    #Validate on the second pass only (when button 'Bewaar' is pushed)
    if 'button' in request.form and request.form['button'] == 'Bewaar' and form.validate_on_submit():
        user = User(email=form.email.data,
                        username=form.username.data,
                        first_name=form.first_name.data,
                        last_name=form.last_name.data,
                        password=form.password.data,
                        is_admin=form.is_admin.data
                    )
        db.session.add(user)
        db.session.commit()
        log.info('add : {}'.format(user.log()))
        #flash('You have added user {}'.format(user.username))
        return redirect(url_for('user.users'))
    return render_template('user/user.html', form=form, title='Voeg een gebruiker toe', role='add', route='user.users', subject='user')


#edit a user
@user.route('/user/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    user = User.query.get_or_404(id)
    form = EditForm(obj=user)
    if form.validate_on_submit():
        if request.form['button'] == 'Bewaar':
            form.populate_obj(user)
            db.session.commit()
            #flash('You have edited user {}'.format(user.username))

        return redirect(url_for('user.users'))
    return render_template('user/user.html', form=form, title='Pas een gebruiker aan', role='edit', route='user.users', subject='user')

#no login required
@user.route('/user/view/<int:id>', methods=['GET', 'POST'])
def view(id):
    user = User.query.get_or_404(id)
    form = ViewForm(obj=user)
    if form.validate_on_submit():
        return redirect(url_for('user.users'))
    return render_template('user/user.html', form=form, title='Bekijk een gebruiker', role='view', route='user.users', subject='user')

#delete a user
@user.route('/user/delete/<int:id>', methods=['GET', 'POST'])
@login_required
def delete(id):
    user = User.query.get_or_404(id)
    db.session.delete(user)
    db.session.commit()
    #flash('You have successfully deleted the user.')
    return redirect(url_for('user.users'))

@user.route('/user/change-password/<int:id>', methods=['GET', 'POST'])
@login_required
def change_pwd(id):
    user = User.query.get_or_404(id)
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if user.verify_password(form.old_password.data):
            user.password = form.new_password.data
            db.session.commit()
            flash('Je paswoord is bewaard.')
            return redirect(url_for('user.users'))
        flash('Ongeldige gebruikersnaam.')
    return render_template('user/user.html', form=form, title='Verander paswoord', role='change_password', route='user.users', subject='user')