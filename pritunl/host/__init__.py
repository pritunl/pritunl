from pritunl.event import Event

from pritunl.host.usage import HostUsage

from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
from pritunl.settings import settings
from pritunl.app_server import app_server
from pritunl.host import keep_alive
from pritunl import utils
from pritunl import mongo
from pritunl import logger

import signal
import datetime

class Host(mongo.MongoObject):
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
        mongo.MongoObject.__init__(self, **kwargs)

        self.usage = HostUsage(self.id)

        if 'id' not in kwargs and 'doc' not in kwargs and 'spec' not in kwargs:
            self.id = app_server.host_id

        if name is not None:
            self.name = name

        if self.name is None:
            self.name = utils.random_name()

    @cached_property
    def user_count(self):
        # TODO
        return 0

    @cached_property
    def users_online(self):
        # TODO
        return 0

    @cached_static_property
    def collection(cls):
        return mongo.get_collection('hosts')

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
            'public_address': self.public_addr,
        }

    def remove(self):
        if self.status == ONLINE:
            raise HostError('Host must be offline to remove')
        MongoObject.remove(self)

    def keep_alive(self):
        keep_alive.start_keep_alive(self)

def get_host(id):
    return Host(id=id)

def iter_hosts():
    for doc in Host.collection.find().sort('name'):
        yield Host(doc=doc)

def init_host():
    hst = Host()

    try:
        hst.load()
    except NotFound:
        pass

    hst.status = ONLINE
    hst.users_online = 0
    hst.start_timestamp = datetime.datetime.utcnow()
    if settings.local.public_ip:
        hst.auto_public_address = settings.local.public_ip

    hst.commit()
    Event(type=HOSTS_UPDATED)

    return hst

def deinit_host():
    hst = Host()

    try:
        hst.load()
    except NotFound:
        pass

    Host.collection.update({
        '_id': hst.id,
    }, {'$set': {
        'status': OFFLINE,
        'ping_timestamp': None,
    }})
