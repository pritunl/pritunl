from pritunl.constants import *
from pritunl.messenger import Messenger
import logging
import time
import uuid

logger = logging.getLogger(APP_NAME)

class Event(object):
    def __init__(self, type, resource_id=None):
        messenger = Messenger('events')
        messenger.publish((type, resource_id))
