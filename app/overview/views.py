from flask import render_template, request, jsonify
from flask_login import login_required

from .. import db, log, mqtt, scheduler
from . import overview
from ..models import  Schedules, Switches
from ..base import get_global_setting_time_start, \
    get_global_setting_time_stop, get_global_setting_time_stop_wednesday, \
    get_global_setting_auto_switch, set_global_setting,get_schedule_settings
import datetime, time, json
from datetime import date, datetime, timedelta
from ..google_calendar import get_holidays
from sqlalchemy import extract

def send_calendar_to_scheduler():
    yesterday = datetime.today() - timedelta(days=1)
    sl = Schedules.query.filter(Schedules.date > yesterday).order_by(Schedules.date).all()
    scheduler.set_scheduler_events(sl)


#show the overview page
@overview.route('/overview/show', methods=['GET', 'POST'])
@login_required
def show():
    #get the switch devices from the datebase
    sdl = None
    try:
        sdl = Switches.query.order_by(Switches.location).all()
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
    send_calendar_to_scheduler()
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
    send_calendar_to_scheduler()

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
        send_calendar_to_scheduler()
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
        send_calendar_to_scheduler()
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
        send_calendar_to_scheduler()
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
        switches_list = Switches.query.order_by(Switches.location).all()
        switches_dict = [i.ret_dict() for i in switches_list]
        for i in range(len(switches_dict)):
            switches_dict[i]['status'] = '<button type="button" class="btn btn-default" onclick="toggle_switch({})">Wijzig</button>'.format(switches_dict[i]['id'])
            switches_dict[i]['DT_RowId'] = switches_dict[i]['id']
            switches_dict[i]['get_status'] = '<p id="get_status{}">UIT</p>'.format(switches_dict[i]['id'])
            switches_dict[i]['get_ip'] = '<p id="get_ip{}">UIT</p>'.format(switches_dict[i]['id'])
    except Exception as e:
        log.error('could not retreive the switches from the database')

    output = {}
    output['draw'] = str(int(request.values['draw']))
    output['recordsTotal'] = str(len(switches_dict))
    output['data'] = switches_dict
    return jsonify(output)

#This route is called to get the data from a single switch
@overview.route('/overview/switch_data/<int:id>', methods=['GET', 'POST'])
@login_required
def switch_data(id):
    log.info('Get the data from switch {}'.format(id))
    try:
        switch = Switches.query.get_or_404(id)
        switch_dict = switch.ret_dict()
    except Exception as e:
        log.error('could not get the data of switch {}'.format(id))
        return jsonify({"status" : False})
    return jsonify({"status" : True, "switch": switch_dict})

#Toggle the state of a switch
@overview.route('/overview/toggle_switch/<int:id>', methods=['GET', 'POST'])
@login_required
def toggle_switch(id):
    log.info('Toggle switch {}'.format(id))
    try:
        switch = Switches.query.get_or_404(id)
        status = mqtt.check_switch_status(switch.name)
        mqtt.set_switch_state(switch.name, not status)
    except Exception as e:
        log.error('could not change toggle switch {}'.format(id))
        return jsonify({"status" : False})

    return jsonify({"status" : True})

#add a new switch
@overview.route('/overview/add_switch/<string:name>/<string:location>', methods=['GET', 'POST'])
@login_required
def add_switch(name, location):
    log.info('add a new switch: {}/{}'.format(name, location))
    try:
        switch = Switches.query.filter(Switches.name==name).first()
        if switch:
            log.error('switch already exists with this name')
            return jsonify({"status" : False})
        switch = Switches(name=name, ip='', location=location, type='sonof_s20')
        db.session.add(switch)
        db.session.commit()
    except Exception as e:
        log.error('could not add the switch')
        return jsonify({"status" : False})

    return jsonify({"status" : True})

#edit a switch
@overview.route('/overview/edit_switch/<int:id>/<string:name>/<string:location>', methods=['GET', 'POST'])
@login_required
def edit_switch(id, name, location):
    log.info('edit a switch: {}/{}/{}'.format(id, name, location))
    try:
        switch = Switches.query.get_or_404(id)
        switch.name = name
        switch.location = location
        db.session.commit()
    except Exception as e:
        log.error('could not  edit the switch')
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

@overview.route('/overview/check_switch_hb_status', methods=['GET', 'POST'])
@login_required
def check_switch_hb_status():
    sl = Switches.query.all()
    switch_list = []
    for s in sl:
        hb = mqtt.check_switch_hb(s.name)
        status = mqtt.check_switch_status(s.name)
        ip = mqtt.get_switch_ip(s.name)
        switch_list.append({'name': s.name, 'id': s.id, 'hb': hb, 'status': status, 'ip': ip})
    return jsonify({"switch_list" : switch_list})

def check_time_format(time):
    try:
        t_s = time.split(':')
        h = int(t_s[0])
        m = int(t_s[1])
    except:
        raise ValueError('Verkeerd formaat ({}), het moet zijn : UU:MM'.format(time))
    return h*60+m

#save settings
@overview.route('/overview/save_settings/<string:settings>', methods=['GET', 'POST'])
@login_required
def save_settings(settings):
    try:
        sched_list = json.loads(settings)
        for i, sched in enumerate(sched_list):
            log.info(f'save settings: {sched["start_time"]}/{sched["stop_time_wednesday"]}/{sched["stop_time"]}/{sched["auto_switch"]}')
            start_time = check_time_format(sched['start_time'])
            stop_time = check_time_format(sched['stop_time'])
            stop_time_wednesday = check_time_format(sched['stop_time_wednesday'])
            if not (start_time < stop_time_wednesday and stop_time_wednesday <= stop_time):
                raise ValueError(f'Fout in lijn {i} : starttijd < stoptijd woensdag <= stoptijd')
            set_global_setting(f'start_time{i}', sched['start_time'])
            set_global_setting(f'stop_time_wednesday{i}', sched['stop_time_wednesday'])
            set_global_setting(f'stop_time{i}', sched['stop_time'])
            set_global_setting(f'auto_switch{i}', sched['auto_switch'])
            scheduler.set_scheduler_settings(sched)
    except ValueError as e:
        return  jsonify({"status" : False, 'message': str(e)})
    except Exception as e:
        log.error('could not save the settings')
        return jsonify({"status" : False})

    return jsonify({"status" : True})

#get the settings
@overview.route('/overview/get_settings', methods=['GET', 'POST'])
@login_required
def get_settings():
    log.info('Get the settings from the database')
    try:
        schedules = get_schedule_settings()
    except Exception as e:
        log.error('could not get the settings')
        return jsonify({"status" : False})
    return jsonify({"status" : True, "schedule": schedules})

@overview.route('/overview/rest_push_events_settings/<string:message>', methods=['GET', 'POST'])
def rest_push_events_settings(message):
    log.info('push the events to the scheduler')
    try:
        send_calendar_to_scheduler()
        settings = {
            'start_time': get_global_setting_time_start(),
            'stop_time': get_global_setting_time_stop(),
            'stop_time_wednesday': get_global_setting_time_stop_wednesday(),
            'auto_switch': get_global_setting_auto_switch()
        }
        scheduler.set_scheduler_settings(settings)
    except Exception as e:
        log.error('error, could not push the events : {}'.format(e))
        return jsonify({'status' : False})

    return jsonify({'status' : True})

