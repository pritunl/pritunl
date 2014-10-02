from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
from pritunl.settings import settings
from pritunl.app import app

import flask

def setup_app():
    if settings.conf.debug and settings.conf.ssl:
        settings.conf.ssl = False
