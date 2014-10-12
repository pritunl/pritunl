from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
from pritunl import settings
from pritunl import utils
from pritunl import logger

import threading
import time
import datetime

def _time_sync_thread():
    while True:
        try:
            utils.sync_time()
        except:
            logger.exception('Failed to sync time with mongo server.')
        time.sleep(15)

def start_time_sync():
    thread = threading.Thread(target=_time_sync_thread)
    thread.daemon = True
    thread.start()
