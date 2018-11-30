# -*- coding: utf-8 -*-

from flask import render_template, redirect, url_for, request, flash, send_file, session, jsonify
from flask_login import login_required, current_user

from .. import db, log
from . import overview
from ..models import  Schedules, Switches
from ..base import build_filter, get_ajax_table
from ..tables_config import  tables_configuration

import cStringIO, csv, re, datetime, time
from datetime import date, datetime, timedelta

from sqlalchemy.exc import IntegrityError
from sqlalchemy import extract

from ..google_calendar import get_holidays


#show the overview page
@overview.route('/overview/show', methods=['GET', 'POST'])
@login_required
def show():
    return render_template('overview/overview.html')

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
    id_count = 1000
    saturdays = weekdayDatesInAYear(year, 5)
    for d in saturdays:
        e = {
            'id': id_count,
            'name': '',
            'location': '',
            'color' : 'red',
            'startDate': time.mktime(d.timetuple()) * 1000,
            'endDate': time.mktime((d + timedelta(days=1)).timetuple()) * 1000,
        }
        id_count += 1
        t.append(e)

    hl = Schedules.query.filter(extract('year', Schedules.date) == year).all()
    for h in hl:
        e = {
            'id': h.id,
            'name': '',
            'location': '',
            'color' : 'red',
            'startDate': time.mktime(h.date.timetuple()) * 1000,
            'endDate': time.mktime((h.date + timedelta(days=h.days)).timetuple()) * 1000,
        }
        t.append(e)

    return jsonify({"calendar" : t})

#This route is called by an ajax call to get the holidays of the current year from a google calendar
@overview.route('/overview/load_calendar_holidays/<int:year>', methods=['GET', 'POST'])
@login_required
def load_calendar_holidays(year):
    print('trying to get the holidays...')
    hl = get_holidays(year)

    for event in hl:
        start_date = datetime.strptime(event['start']['date'], '%Y-%m-%d')
        if start_date.year < year:
            start_date = datetime(year, 1, 1)
        end_date = datetime.strptime(event['end']['date'], '%Y-%m-%d')
        if end_date.year > year:
            end_date = datetime(year + 1, 1, 1)
        days = (end_date - start_date).days

        #is holiday already in database, then skip
        hd = Schedules.query.filter_by(date=start_date, days=days).first()
        if not hd:
            hd = Schedules(date=start_date, days=days)
            db.session.add(hd)
        db.session.commit()

        print (start_date, days, event['summary'])

    return jsonify({"status" : True})


# #This route is called by an ajax call on the assets-page to populate the table.
# @overview.route('/overview/data', methods=['GET', 'POST'])
# @login_required
# def source_data():
#     return get_ajax_table(tables_configuration['overview'])
#
# #show a list of registrations
# @overview.route('/overview/registrations', methods=['GET', 'POST'])
# @login_required
# def registrations():
#     #The following line is required only to build the filter-fields on the page.
#     _filter, _filter_form, a,b, c = build_filter(tables_configuration['overview'])
#     return render_template('base_multiple_items.html',
#                            title='registraties',
#                            filter=_filter, filter_form=_filter_form,
#                            config = tables_configuration['overview'])
#
# #start timer
# @overview.route('/overview/start/<int:id>', methods=['GET', 'POST'])
# @login_required
# def start(id):
#     try:
#         series = Series.query.get(id)
#         if not series.running:
#             series.running = True
#             series.starttime = datetime.datetime.now()
#             db.session.commit()
#     except Exception as e:
#         log.error('cannot start timer of series : {} error {}'.format(series.name, e))
#     return jsonify('ok')
#
# #stop timer
# @overview.route('/overview/reset/<int:id>', methods=['GET', 'POST'])
# @login_required
# def reset(id):
#     try:
#         series = Series.query.get(id)
#         series.running = False
#         series.starttime = None
#         db.session.commit()
#     except Exception as e:
#         log.error('cannot start/stop timer of series : {} error {}'.format(series.name, e))
#     return jsonify('ok')
#
#
#
# #Get the timer values for the different series
# @overview.route('/overview/get_timer', methods=['GET', 'POST'])
# @login_required
# def get_timer():
#     t = {}
#     series = Series.query.order_by(Series.sequence).all()
#     nw = datetime.datetime.now()
#     for s in series:
#         if s.running:
#             d = (nw - s.starttime)
#             m  = int(d.seconds/60)
#             sec = d.seconds - m * 60 + 1
#             if d.days < 0:
#                 m = 0
#                 sec = 1
#             if sec > 59:
#                 m += 1
#                 sec = 0
#             t[s.id] = '{:02d}:{:02d}'.format(m, sec)
#         else:
#             t[s.id] = '00:00'
#     return jsonify(t)
#
# #give a student a new rfid code
# @overview.route('/overview/new_rfid/<int:id>/<string:result>', methods=['GET', 'POST'])
# @login_required
# def new_rfid(id, result):
#     try:
#         is_valide_code, is_rfid_code, code = process_code(result)
#         if is_rfid_code and is_valide_code:
#             overview = Registration.query.get(id)
#             overview.rfidcode2 = code
#             db.session.commit()
#     except Exception as e:
#         db.session.rollback()
#         flash('Kan nieuwe RFID niet opslaan of RFID bestaat al')
#         log.error('cannot update rfid code: {}'.format(e))
#
#     _filter, _filter_form, a,b, c = build_filter(tables_configuration['overview'])
#     return render_template('base_multiple_items.html',
#                            title='registraties',
#                            filter=_filter, filter_form=_filter_form,
#                            config = tables_configuration['overview'])
#
# #delete the rfid code of a student
# @overview.route('/overview/delete_rfid/<int:id>', methods=['GET', 'POST'])
# @login_required
# def delete_rfid(id):
#     try:
#         overview = Registration.query.get(id)
#         overview.rfidcode2 = None
#         db.session.commit()
#     except Exception as e:
#         flash('Kan RFID niet verwijderen')
#         log.error('cannot delete rfid code: {}'.format(e))
#
#     _filter, _filter_form, a,b, c = build_filter(tables_configuration['overview'])
#     return render_template('base_multiple_items.html',
#                            title='registraties',
#                            filter=_filter, filter_form=_filter_form,
#                            config = tables_configuration['overview'])
#
# #delete the time ran of a student
# @overview.route('/overview/delete_time_ran/<int:id>', methods=['GET', 'POST'])
# @login_required
# def delete_time_ran(id):
#     try:
#         overview = Registration.query.get(id)
#         overview.time_ran = None
#         overview.time_registered = None
#         db.session.commit()
#     except Exception as e:
#         flash('Kan tijd niet verwijderen')
#         log.error('cannot delete  time ran : {}'.format(e))
#
#     _filter, _filter_form, a,b, c = build_filter(tables_configuration['overview'])
#     return render_template('base_multiple_items.html',
#                            title='registraties',
#                            filter=_filter, filter_form=_filter_form,
#                            config = tables_configuration['overview'])
#
#
#
# #show a list of registrations
# @overview.route('/overview', methods=['GET', 'POST'])
# @login_required
# def register():
#
#     registration_succes = 1
#     try:
#         if 'code' in request.form:
#             is_valid_code, is_rfid_code, code = process_code(request.form['code'])
#             #print('{} {} {}'.format(is_valid_code, is_rfid_code, code))
#
#             reg = Registration.query.join(Series)
#             if is_rfid_code:
#                 reg2 = reg.filter(Registration.rfidcode2 == code).first()
#                 if not reg2:
#                     reg2 = reg.filter(Registration.rfidcode == code).first()
#             else:
#                 #code is a student code
#                 reg2 = reg.filter(Registration.studentcode == code).first()
#             if reg2:
#                 #print(u'{}'.format(reg2))
#                 now = datetime.datetime.now()
#                 starttime = reg2.series.starttime
#                 d = now - starttime
#                 reg2.time_ran = d.seconds * 1000 + d.microseconds/1000
#                 reg2.time_registered = now
#                 db.session.commit()
#             else:
#                 registration_succes = 0
#     except Exception as e:
#         log.error(u'Cannot register student: {}'.format(e))
#         registration_succes = 0
#
#     series = Series.query.order_by(Series.sequence).all()
#     registrations=[]
#
#     registrations = Registration.query.filter(Registration.time_registered > 0).order_by(Registration.time_registered.desc()).slice(0, 30).all()
#     return render_template('overview/overview.html',
#                            registration_succes = registration_succes,
#                            series = series,
#                            registrations=registrations)
#
#
# def process_code(code):
#     def process_int_code(code):
#         if int(code) < 100000:
#             #Assumed a student code because it is less then 100.000
#             return False, code
#         h = '{:0>8}'.format(hex(int(code)).split('x')[-1].upper())
#         code = h[6:8] + h[4:6] + h[2:4] + h[0:2]
#         return True, code
#
#     def decode_caps_lock(code):
#         out = u''
#         dd = {u'&': '1', u'É': '2', u'"': '3', u'\'': '4', u'(': '5', u'§': '6', u'È': '7', u'!': '8', u'Ç': '9',
#               u'À': '0', u'A' : 'A', u'B' : 'B', u'C' : 'C', u'D' : 'D', u'E' : 'E', u'F' : 'F'}
#         for i in code:
#             out += dd[i]
#         return out
#
#     is_rfid_code = True
#     is_valid_code = True
#     code = code.upper()
#
#     if len(code) == 8:
#         #Assumed a HEX code of 8 characters
#         if 'Q' in code:
#             # This is a HEX code, with the Q iso A
#             code = code.replace('Q', 'A')
#         try:
#             #Code is ok
#             int(code, 16)
#         except:
#             try:
#                 # decode because of strange characters (CAPS LOCK)
#                 code = decode_caps_lock(code)
#                 int(code, 16)
#             except:
#                 #It shoulde be a HEX code but it is not valid
#                 is_valid_code = False
#     else:
#         #Assumed an INT code
#         try:
#             #code is ok
#             int(code)
#             is_rfid_code, code = process_int_code(code)
#         except:
#             try:
#                 # decode because of strange characters (CAPS LOCK)
#                 code = decode_caps_lock(code)
#                 #code is ok
#                 int(code)
#                 is_rfid_code, code = process_int_code(code)
#             except:
#                 #It should be an INT code but it is not valid
#                 is_valid_code = False
#
#     return is_valid_code, is_rfid_code, code
