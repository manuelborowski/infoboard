# -*- coding: utf-8 -*-

import paho.mqtt.client as mqtt
from requests import Session
import json
from threading import Lock

import time, datetime

class Mqtt:
    HB_COUNTER_RESET = 5

    def __init__(self, app, log):
        self.app = app
        self.log = log
        self.rest = Rest(app)
        self.wait_on_connect = True
        self.switch_dict = {}
        self.switch_lock = Lock()

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print('connected ok')
            # client.subscribe('/sonoff1/drukknop/state')
            # client.subscribe('/sonoff1/relaisin/state')
            #client.subscribe('/sonoff0/uptime')
            self.wait_on_connect = False

    def on_message(self, client, userdata, message):
        if message.topic.find('uptime') > 0:
            #self.rest.set_switch_alive(message.topic.split('/')[1])
            switch = message.topic.split('/')[1]
            self.switch_lock.acquire()
            self.switch_dict[switch] = Mqtt.HB_COUNTER_RESET
            self.switch_lock.release()

    def check_hb_counter(self, switch):
        switch_status = True
        self.switch_lock.acquire()
        if switch in self.switch_dict:
            self.switch_dict[switch] -= 1
            if self.switch_dict[switch] < 1:
                switch_status = False
                self.switch_dict[switch] = 0
        else:
            switch_status = False
        self.switch_lock.release()
        return switch_status

    def start(self):
        self.log.info('Start MQTT client')
        self.client = mqtt.Client('infoboard')
        self.client.on_connect=self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(self.app.config['MQTT_SERVER'])
        #Wait until client is connected, this takes less than a millisecond
        while not self.wait_on_connect:
            time.sleep(1)
        self.client.loop_start()

    def subscribe_to_switches(self):
        self.log.info('MQTT : subscribing to all switches')
        self.client.subscribe('/+/uptime')
        self.client.subscribe('/+/relaisin')


class Rest:
    def __init__(self, app):
        self.app = app
        self.session = Session()
        self.server_address = 'http://localhost:{}'.format(self.app.config['SERVER_PORT'])

    def set_switch_alive(self, switch_name):
        d = {}
        d['name'] = switch_name
        return self._set('rest_switch_alive', d)

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

