# -*- coding: utf-8 -*-

import paho.mqtt.client as mqtt
from threading import Lock

import time, datetime,json

class EspEasy:
    HB_COUNTER_RESET = 5

    def __init__(self, app, log):
        self.app = app
        self.log = log
        self.wait_on_connect = True
        self.switch_hb_dict = {}
        self.switch_status_dict = {}
        self.switch_ip_dict = {}
        self.switch_lock = Lock()

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.log.info('MQTT client connected')
            self.wait_on_connect = False

    def on_message(self, client, userdata, message):
        try:
            self.switch_lock.acquire()
            if message.topic.find('status') > 0:
                switch = message.topic.split('/')[1]
                payload = str(message.payload.decode("utf-8")).split(',')
                status = int(payload[1])
                self.switch_hb_dict[switch] = EspEasy.HB_COUNTER_RESET
                self.switch_status_dict[switch] = True if status == 1 else False
                self.switch_ip_dict[switch] = payload[0]
            if message.topic.find('relaisin') > 0:
                switch = message.topic.split('/')[1]
                status = int(str(message.payload.decode("utf-8")))
                self.switch_hb_dict[switch] = EspEasy.HB_COUNTER_RESET
                self.switch_status_dict[switch] = True if status == 1 else False
        except Exception as e:
            self.log.info('error : {}'.format(e))
        finally:
            self.switch_lock.release()

    #needs to be called at regular interval to sample the heartbeat
    def hb_timer_tick(self):
        try:
            self.switch_lock.acquire()
            for switch in self.switch_hb_dict:
                self.switch_hb_dict[switch] -= 1
                if self.switch_hb_dict[switch] < 1:
                    self.switch_hb_dict[switch] = 0
                    self.switch_ip_dict[switch] = '0.0.0.0'
        except Exception as e:
            self.log.info('error : {}'.format(e))
        finally:
            self.switch_lock.release()
        return


    def check_switch_hb(self, switch):
        switch_hb = True
        try:
            self.switch_lock.acquire()
            if switch in self.switch_hb_dict:
                if self.switch_hb_dict[switch] < 1:
                    switch_hb = False
            else:
                switch_hb = False
        except Exception as e:
            self.log.info('error : {}'.format(e))
        finally:
            self.switch_lock.release()
        return switch_hb

    def check_switch_status(self, switch):
        switch_status = False
        try:
            self.switch_lock.acquire()
            if switch in self.switch_status_dict:
                switch_status = self.switch_status_dict[switch]
        except Exception as e:
            self.log.info('error : {}'.format(e))
        finally:
            self.switch_lock.release()
        return switch_status

    def get_switch_ip(self, switch):
        switch_ip = '0.0.0.0'
        try:
            self.switch_lock.acquire()
            if switch in self.switch_ip_dict:
                switch_ip = self.switch_ip_dict[switch]
        except Exception as e:
            self.log.info('error : {}'.format(e))
        finally:
            self.switch_lock.release()
        return switch_ip

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

    def stop(self):
        self.log.info('Stop MQTT client')
        self.client.loop_stop()

    def subscribe_to_switches(self):
        self.log.info('MQTT : subscribing to all switches')
        self.client.subscribe('/+/uptime')
        self.client.subscribe('/+/relaisin/state')
        self.client.subscribe('/+/status')

    def set_all_switches_state(self, state):
        try:
            self.switch_lock.acquire()
            for s in self.switch_status_dict:
                self.set_switch_state(s, state)
        except Exception as e:
            self.log.info('error : {}'.format(e))
        finally:
            self.switch_lock.release()

    def set_switch_state(self, switch, state):
        self.log.info("MQTT TX : switch {} to state {}".format(switch, state))
        message = "1" if state else "0"
        self.client.publish('/{}/gpio/12'.format(switch), message, retain=True)


class Tasmota:
    HB_COUNTER_RESET = 5

    def __init__(self, app, log):
        self.app = app
        self.log = log
        self.wait_on_connect = True
        self.switch_hb_dict = {}
        self.switch_status_dict = {}
        self.switch_ip_dict = {}
        self.switch_lock = Lock()

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.log.info('MQTT client connected')
            self.wait_on_connect = False

    def on_message(self, client, userdata, message):
        try:
            self.switch_lock.acquire()
            if message.topic.find('RESULT') > 0:
                switch = message.topic.split('/')[1]
                payload = json.loads(str(message.payload.decode("utf-8")))
                if 'POWER' in payload:
                    status = True if payload['POWER'] == 'ON' else False
                    self.switch_hb_dict[switch] = Tasmota.HB_COUNTER_RESET
                    self.switch_status_dict[switch] = status
                    # self.switch_ip_dict[switch] = payload[0]
            if message.topic.find('STATUS5') > 0:
                switch = message.topic.split('/')[1]
                payload = json.loads(str(message.payload.decode("utf-8")))
                if 'StatusNET' in payload:
                    self.switch_hb_dict[switch] = Tasmota.HB_COUNTER_RESET
                    self.switch_ip_dict[switch] = payload['StatusNET']['IPAddress']
        except Exception as e:
            self.log.info('error : {}'.format(e))
        finally:
            self.switch_lock.release()

    #needs to be called at regular interval to sample the heartbeat
    def hb_timer_tick(self):
        for switch in self.switch_hb_dict:
            self.request_status(switch)
            self.request_state(switch)
        try:
            self.switch_lock.acquire()
            for switch in self.switch_hb_dict:
                self.switch_hb_dict[switch] -= 1
                if self.switch_hb_dict[switch] < 1:
                    self.switch_hb_dict[switch] = 0
                    self.switch_ip_dict[switch] = '0.0.0.0'
        except Exception as e:
            self.log.info('error : {}'.format(e))
        finally:
            self.switch_lock.release()
        return


    def check_switch_hb(self, switch):
        switch_hb = True
        try:
            self.switch_lock.acquire()
            if switch in self.switch_hb_dict:
                if self.switch_hb_dict[switch] < 1:
                    switch_hb = False
            else:
                self.switch_hb_dict[switch] = Tasmota.HB_COUNTER_RESET
                switch_hb = False
        except Exception as e:
            self.log.info('error : {}'.format(e))
        finally:
            self.switch_lock.release()
        return switch_hb

    def check_switch_status(self, switch):
        switch_status = False
        try:
            self.switch_lock.acquire()
            if switch in self.switch_status_dict:
                switch_status = self.switch_status_dict[switch]
        except Exception as e:
            self.log.info('error : {}'.format(e))
        finally:
            self.switch_lock.release()
        return switch_status

    def get_switch_ip(self, switch):
        switch_ip = '0.0.0.0'
        try:
            self.switch_lock.acquire()
            if switch in self.switch_ip_dict:
                switch_ip = self.switch_ip_dict[switch]
        except Exception as e:
            self.log.info('error : {}'.format(e))
        finally:
            self.switch_lock.release()
        return switch_ip

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

    def stop(self):
        self.log.info('Stop MQTT client')
        self.client.loop_stop()

    def subscribe_to_switches(self):
        self.log.info('MQTT : subscribing to all switches')
        self.client.subscribe('stat/+/RESULT')
        self.client.subscribe('stat/+/STATUS5')

    def set_all_switches_state(self, state):
        for s in self.switch_status_dict:
            self.set_switch_state(s, state)

    # warning : no protection with lock!
    def set_switch_state(self, switch, state):
        self.log.info("MQTT TX : switch {} to state {}".format(switch, state))
        message = "ON" if state else "OFF"
        self.client.publish(f'cmnd/{switch}/power', message, retain=True)

    # warning : no protection with lock!
    def request_status(self, switch):
        self.log.info(f"MQTT TX : request status of switch {switch}")
        message = 5  # network information
        self.client.publish(f'cmnd/{switch}/status', message, retain=False)

    # warning : no protection with lock!
    def request_state(self, switch):
        self.log.info(f"MQTT TX : request state of switch {switch}")
        message = '?'
        self.client.publish(f'cmnd/{switch}/state', message, retain=False)
