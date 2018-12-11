# -*- coding: utf-8 -*-

from threading import Thread, Lock
from time import sleep
from requests import Session
import json
from datetime import datetime


def thread_function(self):
    self.log.info('Start Scheduler Thread')
    self.rest.force_push_events_settings()
    while True:
        sleep(5)
        #required to check if a switch is still alive
        self.mqtt.hb_timer_tick()

        #scheduler
        settings = self.get_scheduler_settings()
        if settings['auto_switch']:
            day = self.get_scheduler_first_event()
            if not day or day.date != datetime.today().date():
                now = datetime.now()
                now_minutes = now.hour * 60 + now.minute
                start_time_minutes = self.time_string_to_minutes(settings['start_time'])
                stop_time_wednesday_minutes = self.time_string_to_minutes(settings['stop_time_wednesday'])
                stop_time_minutes = self.time_string_to_minutes(settings['stop_time'])
                is_wednesday = True if now.weekday() == 3 else False
                if self.schedule_on:
                    if is_wednesday:
                        if now_minutes >= stop_time_wednesday_minutes:
                            self.log.info('disable infoboard, ON wednesday {}'.format(now))
                            self.schedule_on = False
                            self.set_all_switches(False)
                    else:
                        if now_minutes >= stop_time_minutes:
                            self.log.info('disable infoboard, NOT on wednesday {}'.format(now))
                            self.schedule_on = False
                            self.set_all_switches(False)
                else:
                    if is_wednesday:
                        if now_minutes >= start_time_minutes and now_minutes < stop_time_wednesday_minutes:
                            self.log.info('enable infoboard ON wednesday {}'.format(now))
                            self.schedule_on = True
                            self.set_all_switches(True)
                    else:
                        if now_minutes >= start_time_minutes and now_minutes < stop_time_minutes:
                            self.log.info('enable infoboard NOT on wednesday {}'.format(now))
                            self.schedule_on = True
                            self.set_all_switches(True)

class Scheduler:
    def __init__(self, mqtt, app, log):
        self.mqtt = mqtt
        self.app = app
        self.log = log
        self.lock = Lock()
        self.settings = {}
        self.events = {}
        self.rest = Rest(app, log)
        self.schedule_on = False

    def start(self):
        self.log.info('Start Scheduler')
        self.thread = Thread(target=thread_function, args=(self, ))
        self.thread.start()

    def set_all_switches(self, status):
        self.mqtt.set_all_switches_state(status)

    def set_scheduler_settings(self, settings):
        try:
            self.lock.acquire()
            self.settings = settings
            if settings['auto_switch']:
                self.schedule_on = False
        except Exception as e:
            self.log.info('error : {}'.format(e))
        finally:
            self.lock.release()

    def get_scheduler_settings(self):
        settings = {}
        try:
            self.lock.acquire()
            settings = self.settings
        except Exception as e:
            self.log.info('error : {}'.format(e))
        finally:
            self.lock.release()
        return settings

    def set_scheduler_events(self, events):
        try:
            self.lock.acquire()
            self.events = events
        except Exception as e:
            self.log.info('error : {}'.format(e))
        finally:
            self.lock.release()

    def get_scheduler_events(self):
        events = {}
        try:
            self.lock.acquire()
            events = self.events
        except Exception as e:
            self.log.info('error : {}'.format(e))
        finally:
            self.lock.release()
        return events

    def get_scheduler_first_event(self):
        try:
            today = datetime.today().date()
            self.lock.acquire()
            if not self.events:
                return_event = None
            elif today > self.events[-1].date:
                self.events = []
                return_event = None
            else:
                for i, event in enumerate(self.events):
                    if today <= event.date:
                        self.events = self.events[i:]
                        return_event = self.events[0]
                        break
        except Exception as e:
            self.log.info('error : {}'.format(e))
        finally:
            self.lock.release()
        return return_event

    def time_string_to_minutes(self, time):
        try:
            t_s = time.split(':')
            h = int(t_s[0])
            m = int(t_s[1])
        except:
            self.log.error('Bad format of ({}), must be UU:MM'.format(time))
        return h*60+m

class Rest:
    def __init__(self, app, log):
        self.app = app
        self.log = log
        self.session = Session()
        self.server_address = 'http://localhost:{}'.format(self.app.config['SERVER_PORT'])

    def force_push_events_settings(self):
        return self._set('rest_push_events_settings', {})

    def _set(self, command, json_message):
        json_string = json.dumps(json_message)
        self.session.head(self.server_address)
        response = self.session.post(
            url='{}/overview/{}/{}'.format(self.server_address, command, json_string),
            headers={'Referer': self.server_address}
        )
        status = json.loads(response.content)
        return status['status']

    def _get(self, command):
        self.session.head(self.server_address)
        response = self.session.post(
            url='{}/overview/{}'.format(self.server_address, command),
            headers={'Referer': self.server_address}
        )
        json_message = json.loads(response.content)
        return json_message
