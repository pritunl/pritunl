from pritunl.server.output import ServerOutput
from pritunl.server.bandwidth import ServerBandwidth
from pritunl.server.ip_pool import ServerIpPool

from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
from pritunl import settings
from pritunl import ipaddress
from pritunl import logger
from pritunl import host
from pritunl import utils
from pritunl import mongo
from pritunl import queue
from pritunl import transaction
from pritunl import event
from pritunl import messenger
from pritunl import organization
from pritunl import listener

import os
import signal
import time
import datetime
import subprocess
import threading
import traceback
import re
import bson
import pymongo
import random
import collections

_resource_locks = collections.defaultdict(threading.Lock)
_interfaces = set(['tun%s' % x for x in xrange(128)])

class ServerInstance(object):
    def __init__(self, server):
        self.server = server
        self.instance_id = str(bson.ObjectId())
        self.resource_lock = None
        self.interrupt = False
        self.clean_exit = False
        self.clients = {}
        self.client_count = 0
        self.interface = None
        self._temp_path = utils.get_temp_path()
        self.thread_semaphores = threading.Semaphore(3)
        for _ in xrange(3):
            self.thread_semaphores.acquire()

    @cached_static_property
    def collection(cls):
        return mongo.get_collection('servers')

    def get_cursor_id(self):
        return messenger.get_cursor_id('servers')

    def publish(self, message, transaction=None, extra=None):
        extra = extra or {}
        extra.update({
            'server_id': self.server.id,
        })
        messenger.publish('servers', message,
            extra=extra, transaction=transaction)

    def subscribe(self, cursor_id=None, timeout=None):
        for msg in messenger.subscribe('servers', cursor_id=cursor_id,
                timeout=timeout):
            if msg.get('server_id') == self.server.id:
                yield msg
