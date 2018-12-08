# -*- coding: utf-8 -*-

from threading import Thread, Lock
from time import sleep
from requests import Session
import json
from datetime import datetime

def thread_function(self):
    self.log.info('Start Scheduler Thread')
    self.rest.force_push_events()
    while True:
        sleep(5)
        #required to check if a switch is still alive
        self.mqtt.hb_timer_tick()

        #scheduler
        day = self.get_scheduler_first_event()
        print(day)

class Scheduler:
    def __init__(self, mqtt, app, log):
        self.mqtt = mqtt
        self.app = app
        self.log = log
        self.lock = Lock()
        self.settings = {}
        self.events = {}
        self.rest = Rest(app)
        self.schedule_on = False

    def start(self):
        self.log.info('Start Scheduler')
        self.thread = Thread(target=thread_function, args=(self, ))
        self.thread.start()

    def set_scheduler_settings(self, settings):
        try:
            self.lock.acquire()
            self.settings = settings
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


class Rest:
    def __init__(self, app):
        self.app = app
        self.session = Session()
        self.server_address = 'http://localhost:{}'.format(self.app.config['SERVER_PORT'])

    def force_push_events(self):
        return self._set('rest_push_events', {})

    def set_switch_status(self, switch_name, status):
        d = {'name': switch_name, 'status': status}
        return self._set('rest_set_switch_status', d)

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
