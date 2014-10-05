from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
from pritunl import settings
from pritunl import listener
from pritunl import logger

import threading

def _check():
    try:
        settings.load_mongo()
    except:
        logger.exception('Auto settings check failed')
    _start_check_timer()

def _start_check_timer():
    thread = threading.Timer(settings.app.settings_check_interval, _check)
    thread.daemon = True
    thread.start()

def start_settings():
    listener.add_listener('setting', settings.on_msg)
    _start_check_timer()