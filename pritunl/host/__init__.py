from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
from pritunl.settings import settings
from pritunl.organization import Organization
from pritunl.host.usage import HostUsage
from pritunl.event import Event
from pritunl.logger.entry import LogEntry
from pritunl.messenger import Messenger
from pritunl.server.bandwidth import ServerBandwidth
from pritunl.server.ip_pool import ServerIpPool
from pritunl.queue.assign_ip_addr import QueueAssignIpAddr
from pritunl.queue.unassign_ip_addr import QueueUnassignIpAddr
from pritunl.queue.assign_ip_pool import QueueAssignIpPool
from pritunl.queue.dh_params import QueueDhParams
from pritunl.mongo.object import MongoObject
from pritunl.mongo.transaction import MongoTransaction
from pritunl.cache import cache_db
from pritunl import app_server
import pritunl.utils as utils
import pritunl.ipaddress as ipaddress
import pritunl.mongo as mongo
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
        'public_address',
        'auto_public_address',
    }
    fields_default = {
        'status': OFFLINE,
    }

    def __init__(self, name=None, **kwargs):
        MongoObject.__init__(self, **kwargs)

        if 'id' not in kwargs and 'doc' not in kwargs and 'spec' not in kwargs:
            self.id = app_server.host_id

        self.usage = HostUsage(self.id)

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

    @cached_static_property
    def usage_collection(cls):
        return mongo.get_collection('hosts_usage')

    @property
    def uptime(self):
        if not self.start_timestamp:
            return
        return max((datetime.datetime.now() - self.start_timestamp).seconds, 1)

    @property
    def public_addr(self):
        return self.public_address or self.auto_public_address

    def dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'status': self.status,
            'uptime': self.uptime,
            'user_count': self.user_count,
            'users_online': self.users_online,
            'public_address': self.public_address or self.auto_public_address,
        }

    def remove(self):
        if self.status == ONLINE:
            raise HostError('Host must be offline to remove')
        MongoObject.remove(self)

    def _get_proc_stat(self):
        try:
            with open('/proc/stat') as stat_file:
                return stat_file.readline().split()[1:]
        except:
            logger.exception('Failed to read proc stat. %r' % {
                'host_id': self.id,
            })

    def _calc_cpu_usage(self, last_proc_stat, proc_stat):
        try:
            deltas = [int(x) - int(y) for x, y in zip(
                proc_stat, last_proc_stat)]
            total = sum(deltas)
            return float(total - deltas[3]) / total
        except:
            logger.exception('Failed to calculate cpu usage')
        return 0

    def _get_mem_usage(self):
        try:
            free = subprocess.check_output(['free']).split()
            return float(free[15]) / float(free[7])
        except:
            logger.exception(
                'Failed to get memory usage. %r' % {
                    'host_id': self.id,
                })
        return 0

    def _keep_alive_thread(self):
        last_update = None
        proc_stat = None

        while True:
            try:
                timestamp = datetime.datetime.utcnow()
                timestamp -= datetime.timedelta(
                    microseconds=timestamp.microsecond,
                    seconds=timestamp.second,
                )
                if timestamp != last_update:
                    last_update = timestamp

                    last_proc_stat = proc_stat
                    proc_stat = self._get_proc_stat()

                    if last_proc_stat and proc_stat:
                        cpu_usage = self._calc_cpu_usage(
                            last_proc_stat, proc_stat)
                        mem_usage = self._get_mem_usage()
                        self.usage.add_period(timestamp, cpu_usage, mem_usage)

                time.sleep(settings.app.host_ttl - 10)

                self.collection.update({
                    '_id': self.id,
                }, {'$set': {
                    'ping_timestamp': datetime.datetime.utcnow(),
                    'auto_public_address': app_server.public_ip,
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
    def get_host(cls, id):
        return cls(id=id)

    @classmethod
    def iter_hosts(cls):
        for doc in cls.collection.find().sort('name'):
            yield cls(doc=doc)

    @classmethod
    def init_host(cls):
        host = cls()

        try:
            host.load()
        except NotFound:
            pass

        host.status = ONLINE
        host.users_online = 0
        host.start_timestamp = datetime.datetime.utcnow()
        host.auto_public_address = app_server.public_ip

        host.commit()
        Event(type=HOSTS_UPDATED)

        return host
