from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
from pritunl.queue import Queue
from pritunl.messenger import Messenger
import pritunl.mongo as mongo
import pymongo
import random
import bson
import datetime
import logging
import threading
import time
import collections

logger = logging.getLogger(APP_NAME)
_channels = collections.defaultdict(set)

def add_listener(channel, callback):
    _channels[channel].add(callback)

def listener_thread():
    messenger = Messenger()

    while True:
        try:
            for msg in messenger.subscribe(_channels.keys()):
                for listener in _channels[msg['channel']]:
                    try:
                        listener(msg)
                    except:
                        logger.exception('Error in listener callback')
        except:
            logger.exception('Error in listener thread.')
            time.sleep(0.3)

def start():
    thread = threading.Thread(target=listener_thread)
    thread.daemon = True
    thread.start()
