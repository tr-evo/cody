"""
config.py
- settings for the flask application object
"""

class BaseConfig(object):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///annotations.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    # used for encryption and session management
    SECRET_KEY = '\x93\xa0A\x8e2A\x92\x85A\xa0\x9b\x05t\xbf\xd5\xbe'