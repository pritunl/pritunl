from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *
from pritunl import listener
from pritunl import logger
from pritunl import messenger

import pymongo
import random
import bson
import datetime
import logging
import threading
import time

@interrupter
def listener_thread():
    while True:
        try:
            for msg in messenger.subscribe(listener.channels.keys()):
                for lstnr in listener.channels[msg['channel']]:
                    try:
                        lstnr(msg)
                    except:
                        logger.exception('Error in listener callback')
        except GeneratorExit:
            raise
        except:
            logger.exception('Error in listener thread')
            time.sleep(0.3)

        yield

def start_listener():
    threading.Thread(target=listener_thread).start()
