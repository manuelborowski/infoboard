# -*- coding: utf-8 -*-
from wtforms.widgets.core import html_params
from wtforms.widgets import HTMLString
from wtforms import BooleanField
from flask import flash,  request, get_flashed_messages, jsonify, url_for
from flask_login import current_user
from sqlalchemy import or_
import time, datetime

from .models import User, Settings
from . import log

class InlineButtonWidget(object):
    """
    Render a basic ``<button>`` field.
    """
    input_type = 'submit'
    html_params = staticmethod(html_params)

    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        kwargs.setdefault('type', self.input_type)
        kwargs.setdefault('value', field.label.text)
        return HTMLString('<input %s>' % self.html_params(name=field.name, **kwargs))


class InlineSubmitField(BooleanField):
    """
    Represents an ``<button type="submit">``.  This allows checking if a given
    submit button has been pressed.
    """
    widget = InlineButtonWidget()

######################################################################################################
###                                       Build a generic filter
######################################################################################################

def check_date_in_form(date_key, form):
    if date_key in form and form[date_key] != '':
        try:
            time.strptime(form[date_key].strip(), '%d-%M-%Y')
            return form[date_key].strip()
        except:
            flash('Verkeerd datumformaat, moet in de vorm zijn : d-m-y')
    return ''

def check_value_in_form(value_key, form):
    if value_key in form and form[value_key] != '':
        try:
            float(form[value_key])
            return form[value_key]
        except:
            flash('Verkeerde getal notatie')
    return ''

def check_string_in_form(value_key, form):
    if value_key in form and form[value_key] != '':
        try:
            isinstance(form[value_key], str)
            return form[value_key]
        except Exception as e:
            flash('Verkeerde tekst notatie')
    return ''

def build_filter(table, paginate=True):
    #depending on the table, multiple joins are required to get the necessary data
    _model = table['model']
    _filters_enabled = table['filter']
    _template = table['template']
    _filtered_list = _model.query

    if 'query_filter' in table:
        _filtered_list = table['query_filter'](_filtered_list)

    _total_count = _filtered_list.count()

    _filter_forms = {}

    #search, if required
    #from template, take order_by and put in a list.  This is user later on, to get the columns in which can be searched
    column_list = [a['order_by'] for a in _template]
    search_value = check_string_in_form('search[value]', request.values)
    if search_value:
        a = search_value.split('-')[::-1]
        a[0] += '%'
        search_value = '%' + search_value + '%'
        search_constraints = []

        if User.username in column_list:
            search_constraints.append(User.username.like(search_value))
        if User.first_name in column_list:
            search_constraints.append(User.first_name.like(search_value))
        if User.last_name in column_list:
            search_constraints.append(User.last_name.like(search_value))
        if User.email in column_list:
            search_constraints.append(User.email.like(search_value))

        if search_constraints:
            _filtered_list = _filtered_list.filter(or_(*search_constraints))

    _filtered_count = _filtered_list.count()

    #order, if required, first stage
    column_number = check_value_in_form('order[0][column]', request.values)
    if column_number:
        column_name = check_string_in_form('columns[' + str(column_number) + '][data]', request.values)
        if _template[int(column_number)]['order_by'] and  not callable(_template[int(column_number)]['order_by']) :
            direction = check_string_in_form('order[0][dir]', request.values)
            if direction == 'desc':
                _filtered_list = _filtered_list.order_by(_template[int(column_number)]['order_by'].desc())
            else:
                _filtered_list = _filtered_list.order_by(_template[int(column_number)]['order_by'])

    if paginate:
        #paginate, if required
        start = check_value_in_form('start', request.values)
        if start:
            length = int(check_value_in_form('length', request.values))
            start = int(start)
            _filtered_list = _filtered_list.slice(start, start+length)


    _filtered_list = _filtered_list.all()

    return _filters_enabled,  _filter_forms, _filtered_list, _total_count, _filtered_count,


def get_ajax_table(table):
    __filters_enabled,  _filter_forms, _filtered_list, _total_count, _filtered_count = build_filter(table)
    _filtered_dict = [i.ret_dict() for i in _filtered_list]
    for i in _filtered_dict:
        for h in table['href']:
            exec("i" + h['attribute'] + "= \"<a href=\\\"{}\\\">{}</a>\".format(url_for(" + h['route'] + ", id=i" + h['id'] + "), i" + h['attribute'] + ')')
        i['DT_RowId'] = i['id']

    # #order, if required, 2nd stage
    _template = table['template']
    column_number = check_value_in_form('order[0][column]', request.values)
    if column_number and _template[int(column_number)]['order_by'] and  callable(_template[int(column_number)]['order_by']):
        reverse = False if check_string_in_form('order[0][dir]', request.values) == 'desc' else True
        _filtered_dict = sorted(_filtered_dict, key= _template[int(column_number)]['order_by'], reverse=reverse)
    output = {}
    output['draw'] = str(int(request.values['draw']))
    output['recordsTotal'] = str(_total_count)
    output['recordsFiltered'] = str(_filtered_count)
    output['data'] = _filtered_dict
    # add the (non-standard) flash-tag to display flash-messages via ajax
    fml = get_flashed_messages()
    if not not fml:
        output['flash'] = fml
    return jsonify(output)

######################################################################################################
###                                       Handle settings
######################################################################################################

from . import db

#return : found, value
# found : if True, setting was found else not
# value ; if setting was found, returns the value
def get_setting(name, id=-1):
    try:
        setting = Settings.query.filter_by(name=name, user_id=id if id > -1 else current_user.id).first()
        if setting.type== Settings.SETTING_TYPE.E_INT:
            value = int(setting.value)
        elif setting.type == Settings.SETTING_TYPE.E_FLOAT:
            value = float(setting.value)
        elif setting.type == Settings.SETTING_TYPE.E_BOOL:
            value = True if setting.value == 'True' else False
        else:
            value = setting.value
    except:
        return False, ''
    return True, value

def add_setting(name, value, type, id=-1):
    setting = Settings(name=name, value=str(value), type=type, user_id=id if id >-1 else current_user.id)
    db.session.add(setting)
    db.session.commit()
    log.info('add : {}'.format(setting.log()))
    return True

def set_setting(name, value, id=-1):
    try:
        setting = Settings.query.filter_by(name=name, user_id=id if id > -1 else current_user.id).first()
        setting.value = value
        db.session.commit()
    except:
        return False
    return True

def get_setting_inc_index_asset_name():
    found, value = get_setting('inc_index_asset_name')
    if found: return value
    add_setting('inc_index_asset_name', True, Settings.SETTING_TYPE.E_BOOL)
    return True

def set_setting_inc_index_asset_name(value):
    return set_setting('inc_index_asset_name', str(value))

def get_setting_copy_from_last_add():
    found, value = get_setting('copy_from_last_add')
    if found: return value
    add_setting('copy_from_last_add', True, Settings.SETTING_TYPE.E_BOOL)
    return True

def set_setting_copy_from_last_add(value):
    return set_setting('copy_from_last_add', str(value))

def get_setting_simulate_dayhour():
    found, value = get_setting('simulate_dayhour')
    if found: return value
    add_setting('simulate_dayhour', '0/0', Settings.SETTING_TYPE.E_STRING)
    return '0/0'

def set_setting_simulate_dayhour(value):
    return set_setting('simulate_dayhour', value)

def set_global_setting(setting, value):
    return set_setting(setting, str(value), 1)

def get_global_setting_current_schoolyear():
    found, value = get_setting('current_schoolyear', 1)
    if found: return value
    add_setting('current_schoolyear', '1718', Settings.SETTING_TYPE.E_STRING, 1)
    return '1718'

def set_global_setting_current_schoolyear(value):
    return set_setting('current_schoolyear', str(value), 1)

def get_global_setting_time_start():
    found, value = get_setting('time_start', 1)
    if found: return value
    add_setting('time_start', '08:00', Settings.SETTING_TYPE.E_STRING, 1)
    return '08:00'

def set_global_setting_time_start(value):
    return set_setting('time_start', str(value), 1)

def get_global_setting_time_stop():
    found, value = get_setting('time_stop', 1)
    if found: return value
    add_setting('time_stop', '16:30', Settings.SETTING_TYPE.E_STRING, 1)
    return '16:30'

def set_global_setting_time_stop(value):
    return set_setting('time_stop', str(value), 1)

def get_global_setting_time_stop_wednesday():
    found, value = get_setting('time_stop_wednesday', 1)
    if found: return value
    add_setting('time_stop_wednesday', '12:30', Settings.SETTING_TYPE.E_STRING, 1)
    return '12:30'

def set_global_setting_time_stop_wednesday(value):
    return set_setting('time_stop_wednesday', str(value), 1)

def get_global_setting_auto_switch():
    found, value = get_setting('auto_switch', 1)
    if found: return value
    add_setting('auto_switch', True, Settings.SETTING_TYPE.E_BOOL, 1)
    return True

def set_global_setting_auto_switch(value):
    return set_setting('auto_switch', str(value), 1)

default_settings = {
    'start_time0': '08:00',
    'start_time1': '08:00',
    'start_time2': '08:00',
    'stop_time_wednesday0': '12:00',
    'stop_time_wednesday1': '12:00',
    'stop_time_wednesday2': '12:00',
    'stop_time0': '16:00',
    'stop_time1': '16:00',
    'stop_time2': '16:00',
    'auto_switch0': 'false',
    'auto_switch1': 'false',
    'auto_switch2': 'false',
}

def get_global_setting(setting):
    found, value = get_setting(setting, 1)
    if found: return value
    add_setting(setting, default_settings[setting], Settings.SETTING_TYPE.E_STRING, 1)
    return default_settings[setting]


def get_schedule_settings():
    settings = []
    for i in range(3):
        setting = {
            'start_time': get_global_setting(f'start_time{i}'),
            'stop_time': get_global_setting(f'stop_time{i}'),
            'stop_time_wednesday': get_global_setting(f'stop_time_wednesday{i}'),
            'auto_switch': get_global_setting(f'auto_switch{i}') == 'True'
        }
        settings.append(setting)
    return settings

######################################################################################################
###                                       Utility functions
######################################################################################################


