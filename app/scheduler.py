# -*- coding: utf-8 -*-

from threading import Thread, Lock
from time import sleep
from requests import Session
import json
from datetime import datetime
from .base import get_schedule_settings


def thread_function(self):
    self.log.info('Start Scheduler Thread')
    sleep(3)
    self.force_push_events_settings()
    first_run = True
    while not self.stop_thread:
        sleep(5)
        #required to check if a switch is still alive
        self.mqtt.hb_timer_tick()

        day = self.get_scheduler_first_event()
        if not day or day.date != datetime.today().date():
            now = datetime.now()
            now_minutes = now.hour * 60 + now.minute
            schedules = get_schedule_settings()
            temp_is_active = False
            for schedule in schedules:
                if schedule['auto_switch']:
                    start_time_minutes = self.time_string_to_minutes(schedule['start_time'])
                    if now.weekday() == 3:
                        stop_time_minutes = self.time_string_to_minutes(schedule['stop_time_wednesday'])
                    else:
                        stop_time_minutes = self.time_string_to_minutes(schedule['stop_time'])
                    if now_minutes >= start_time_minutes and now_minutes < stop_time_minutes:
                        temp_is_active = True
                        break
            if temp_is_active != self.current_schedule_is_active or first_run:
                self.current_schedule_is_active = temp_is_active
                self.log.info(f'Switches go to {"ON" if temp_is_active else "OFF"} state at {now}')
                self.set_all_switches(temp_is_active)
                first_run = False
    self.log.info('Stop Scheduler Thread')


class Scheduler:
    def __init__(self, mqtt, app, log):
        self.mqtt = mqtt
        self.app = app
        self.log = log
        self.lock = Lock()
        self.settings = {}
        self.events = {}
        self.current_schedule_is_active = False
        self.tc = app.test_client()
        self.stop_thread = False

    def start(self):
        self.log.info('Start Scheduler')
        self.thread = Thread(target=thread_function, args=(self, ))
        self.thread.start()

    def stop(self):
        self.log.info('Stop Scheduler')
        self.stop_thread = True
        self.thread.join()

    def set_all_switches(self, status):
        self.mqtt.set_all_switches_state(status)

    def set_scheduler_settings(self, settings):
        try:
            self.lock.acquire()
            self.settings = settings
            if settings['auto_switch']:
                self.current_schedule_is_active = False
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

    def force_push_events_settings(self):
        response = self.tc.get('/overview/rest_push_events_settings/{}'.format(json.dumps({})))
        status = json.loads(response.data.decode('utf-8'))
        return status['status']

