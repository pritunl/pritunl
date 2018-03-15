from pritunl.helpers import *
from pritunl import settings
from pritunl import listener
from pritunl import logger

import threading

@interrupter
def _check():
    yield

    try:
        settings.reload_mongo()
    except:
        logger.exception('Settings check failed', 'runners')

    _start_check_timer()

def _start_check_timer():
    thread = threading.Timer(settings.app.settings_check_interval, _check)
    thread.daemon = True
    thread.start()

def start_settings():
    listener.add_listener('setting', settings.on_msg)
    _start_check_timer()
