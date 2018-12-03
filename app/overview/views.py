# -*- coding: utf-8 -*-

from flask import render_template, redirect, url_for, request, flash, send_file, session, jsonify
from flask_login import login_required, current_user

from .. import db, log
from . import overview
from ..models import  Schedules, Switches
from ..base import build_filter, get_ajax_table
from ..tables_config import  tables_configuration
from .forms import AddForm, EditForm

import cStringIO, csv, re, datetime, time
from datetime import date, datetime, timedelta

from sqlalchemy.exc import IntegrityError
from sqlalchemy import extract, or_


from ..google_calendar import get_holidays


#show the overview page
@overview.route('/overview/show', methods=['GET', 'POST'])
@login_required
def show():
    #get the switch devices from the datebase
    sdl = None
    try:
        sdl = Switches.query.order_by(Switches.name).all()
    except Exception as e:
        log.error('Could not get the switch devices from the database')

    return render_template('overview/overview.html',
                           switches=sdl)

def weekdayDatesInAYear(year, day):
    d = date(year, 1, 1)
    d += timedelta(days = (day - d.weekday() if d.weekday() <= day else 7 + day - d.weekday()))
    while d.year == year:
        yield d
        d += timedelta(days = 7)

#This route is called by an ajax call to populate the calendar
@overview.route('/overview/get_calendar_data/<int:year>', methods=['GET', 'POST'])
@login_required
def get_calendar_data(year):
    t = []
    hl = Schedules.query.filter(extract('year', Schedules.date) == year).all()
    for h in hl:
        e = {
            'id': h.id,
            'name': '',
            'location': '',
            'color' : 'red',
            'startDate': time.mktime(h.date.timetuple()) * 1000,
            'endDate': time.mktime((h.date + timedelta(days=0)).timetuple()) * 1000,
        }
        t.append(e)

    return jsonify({"calendar" : t})

#This route is called by an ajax call to get the holidays of the current year from a google calendar
#and to get all the weekends of said year
@overview.route('/overview/load_calendar/<int:year>', methods=['GET', 'POST'])
@login_required
def load_calendar(year):
    log.info('trying to get the holidays and weekends of given year')

    #Get holidays from google calendar and put in database
    hl = []
    try:
        hl = get_holidays(year)
    except Exception as e:
        log.error('Could not get access to google calendar: {}'.format(e))
        return jsonify({"status": False})

    for event in hl:
        start_date = datetime.strptime(event['start']['date'], '%Y-%m-%d')
        if start_date.year < year:
            start_date = datetime(year, 1, 1)
        end_date = datetime.strptime(event['end']['date'], '%Y-%m-%d')
        if end_date.year > year:
            end_date = datetime(year + 1, 1, 1)

        for d in range(int((end_date - start_date).days)):
            #if holiday is already in database, then skip
            hd = Schedules.query.filter_by(date=(start_date + timedelta(days=d)), days=1).first()
            if not hd:
                hd = Schedules(date=(start_date + timedelta(days=d)), days=1)
                db.session.add(hd)

    #calculate weekenddays and put in database
    t = []
    saturdays = weekdayDatesInAYear(year, 5)
    for d in saturdays:
        for i in range(2):
            # if weekendday is already in database, then skip
            hd = Schedules.query.filter_by(date=(d + timedelta(days=i)), days=1).first()
            if not hd:
                hd = Schedules(date=(d + timedelta(days=i)), days=1)
                db.session.add(hd)

    db.session.commit()

    return jsonify({"status" : True})


#This route is called by an ajax call to delete given calendaryear
@overview.route('/overview/clear_calendar/<int:year>', methods=['GET', 'POST'])
@login_required
def clear_calendar(year):
    log.info('clear the given calendar year')
    try:
        hl = Schedules.query.filter(extract('year', Schedules.date) == year).all()
        for e in hl:
            db.session.delete(e)
        db.session.commit()
    except Exception as e:
        log.error('Could not delete the given calendar year: {}'.format(e))
        return jsonify({"status": False})
    return jsonify({"status": True})


#This route is called by an ajax call to add a date to the database
@overview.route('/overview/add_event/<string:date_string>', methods=['GET', 'POST'])
@login_required
def add_event(date_string):
    try:
        date_string = date_string.split('GMT')[0]
        date = datetime.strptime(date_string, '%a %b %d %Y 00:00:00 ')
        log.info('Adding date: {}'.format(date))
        hd = Schedules.query.filter_by(date=date, days=1).first()
        if hd : raise Exception('event already exists')
        hd = Schedules(date=date, days=1)
        db.session.add(hd)
        db.session.commit()
    except Exception as e:
        log.error('Could not save new event: {}'.format(e))
        return jsonify({"status" : False})

    return jsonify({"status" : True})

#This route is called by an ajax call to delete a date from the database
@overview.route('/overview/delete_event/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_event(id):
    log.info('deleting date: {}'.format(id))
    try:
        hd = Schedules.query.filter_by(id=id).first()
        if not hd : raise Exception('event does not exist')
        db.session.delete(hd)
        db.session.commit()
    except Exception as e:
        log.error('Could not delete event: {}'.format(e))
        return jsonify({"status" : False})

    return jsonify({"status" : True})


#This route is called to get the switches data from the database
@overview.route('/overview/switches_data', methods=['GET', 'POST'])
@login_required
def switches_data():
    log.info('Get the switches data from the database and display')
    switches_dict = {}
    try:
        switches_list = Switches.query.all()
        switches_dict = [i.ret_dict() for i in switches_list]
        for i in xrange(len(switches_dict)):
            #switches_dict[i]['status'] = '<a href="/overview/show">' + str(switches_dict[i]['status']) + '</a>'

            switches_dict[i]['status'] = '<input type="checkbox" id="switch{}" value="1" {} onclick="switch_click({})">'\
                .format(switches_dict[i]['id'], 'checked' if switches_dict[i]['status'] else '',switches_dict[i]['id'] )
            switches_dict[i]['DT_RowId'] = switches_dict[i]['id']
    except Exception as e:
        log.error('could not retreive the switches from the database')

    output = {}
    output['draw'] = str(int(request.values['draw']))
    output['recordsTotal'] = str(len(switches_dict))
    output['data'] = switches_dict
    return jsonify(output)

@overview.route('/overview/change_switch_status/<int:id>/<string:status>', methods=['GET', 'POST'])
@login_required
def change_switch_status(id, status):
    log.info('Change switch {} to status {}'.format(id, status))
    try:
        switch = Switches.query.get_or_404(id);
        switch.status = True if status == 'true' else False
        db.session.commit()
    except Exception as e:
        log.error('could not change the state of switch {} to {}'.format(id, status))
        return jsonify({"status" : False})

    return jsonify({"status" : True})


#add a new switch
@overview.route('/overview/add_switch/<string:name>/<string:ip>/<string:location>', methods=['GET', 'POST'])
@login_required
def add_switch(name, ip, location):
    log.info('add a new switch: {}/{}/{}'.format(name, ip, location))
    try:
        switch = Switches.query.filter(or_(Switches.name==name, Switches.ip==ip)).first()
        if switch:
            log.error('switch already exists with this name or ip')
            return jsonify({"status" : False})
        switch = Switches(name=name, ip=ip, location=location, type='sonof_s20', status=False)
        db.session.add(switch)
        db.session.commit()
    except Exception as e:
        log.error('could not add the switch')
        return jsonify({"status" : False})

    return jsonify({"status" : True})

@overview.route('/overview/delete_switch/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_switch(id):
    log.info('delete switch {}'.format(id))
    try:
        switch = Switches.query.get_or_404(id);
        db.session.delete(switch)
        db.session.commit()
    except Exception as e:
        log.error('could not delete the switch {}'.format(id))
        return jsonify({"status" : False})

    return jsonify({"status" : True})

