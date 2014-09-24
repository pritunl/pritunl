from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
from pritunl.settings import settings
from pritunl.organization import Organization
from pritunl.event import Event
from pritunl.log_entry import LogEntry
from pritunl.messenger import Messenger
from pritunl.server_bandwidth import ServerBandwidth
from pritunl.server_ip_pool import ServerIpPool
from pritunl.queue_assign_ip_addr import QueueAssignIpAddr
from pritunl.queue_unassign_ip_addr import QueueUnassignIpAddr
from pritunl.queue_assign_ip_pool import QueueAssignIpPool
from pritunl.queue_dh_params import QueueDhParams
from pritunl.mongo_object import MongoObject
from pritunl.mongo_transaction import MongoTransaction
from pritunl.cache import cache_db
from pritunl import app_server
import pritunl.utils as utils
import pritunl.ipaddress as ipaddress
import mongo
import uuid
import os
import signal
import time
import datetime
import subprocess
import threading
import logging
import traceback
import re
import json
import bson

logger = logging.getLogger(APP_NAME)

class Host(MongoObject):
    fields = {
        'name',
        'ping_timestamp',
        'status',
        'start_timestamp',
    }
    fields_default = {
        'status': OFFLINE,
    }

    def __init__(self, name=None, **kwargs):
        MongoObject.__init__(self, **kwargs)

        if name is not None:
            self.name = name

        if self.name is None:
            self.name = utils.random_name()

    @cached_property
    def user_count(self):
        return 0

    @cached_property
    def users_online(self):
        return 0

    @cached_static_property
    def collection(cls):
        return mongo.get_collection('hosts')

    @property
    def uptime(self):
        if not self.start_timestamp:
            return
        return max((datetime.datetime.now() - self.start_timestamp).seconds, 1)

    def dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'status': self.status,
            'start_timestamp': self.start_timestamp,
            'user_count': self.user_count,
            'users_online': self.users_online,
        }

    def _keep_alive_thread(self):
        while True:
            time.sleep(settings.app.host_ttl - 10)

            try:
                self.collection.update({
                    '_id': self.id,
                }, {'$set': {
                    'ping_timestamp': datetime.datetime.utcnow(),
                }})
            except:
                logger.exception('Error in host keep alive update. %s' % {
                    'host_id': self.id,
                    'host_name': self.name,
                })

    def keep_alive(self):
        thread = threading.Thread(target=self._keep_alive_thread)
        thread.daemon = True
        thread.start()

    @classmethod
    def init_host(cls):
        host = cls()
        host.id = app_server.host_id
        try:
            host.load()
        except NotFound:
            pass
        host.status = ONLINE
        host.users_online = 0
        host.start_timestamp = datetime.datetime.utcnow()

        host.commit()

        return host
