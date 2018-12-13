# -*- coding: utf-8 -*-

DB_TOOLS = False


class Config(object):
    """
    Common configurations
    """
    STATIC_PATH = "app/static"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LOG_LEVEL = "INFO"
    MQTT_SERVER = "localhost"

class DevelopmentConfig(Config):
    """
    Development configurations
    """
    DEBUG = True
    SQLALCHEMY_ECHO = False
    SERVER_PORT = 5000


class ProductionConfig(Config):
    """
    Production configurations
    """
    DEBUG = False
    SERVER_PORT = 5005


app_config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig
    }
