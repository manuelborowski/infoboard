# -*- coding: utf-8 -*-

DB_TOOLS = False


class Config(object):
    """
    Common configurations
    """
    STATIC_PATH = "app/static"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LOG_LEVEL = "INFO"

class DevelopmentConfig(Config):
    """
    Development configurations
    """
    DEBUG = True
    SQLALCHEMY_ECHO = False


class ProductionConfig(Config):
    """
    Production configurations
    """
    DEBUG = False


app_config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig
    }
