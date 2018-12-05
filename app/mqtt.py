# -*- coding: utf-8 -*-

import paho.mqtt.client as mqtt
from flask import current_app
#from models import Switches

class Mqtt:
    def __init__(self, app, log):
        self.app = app
        self.log = log

    def start(self):
        self.log.info('Start MQTT client')
#        self.client = mqtt.Client('Infoboard')
#        self.client.connect(self.app.config['MQTT_SERVER'])
#        with self.app.app_context():
#            print current_app.name
#         sl = Switches.query.all()
#         for s in sl:
#             print s.name