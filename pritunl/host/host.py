from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
from pritunl.settings import settings
from pritunl.host.usage import HostUsage
from pritunl.event import Event
from pritunl.mongo.object import MongoObject
from pritunl.app_server import app_server
import pritunl.host.keep_alive as keep_alive
import pritunl.utils as utils
import pritunl.mongo as mongo
import signal
import datetime
import logging

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
        if app_server.public_ip:
            host.auto_public_address = app_server.public_ip

        host.commit()
        Event(type=HOSTS_UPDATED)

        return host

    @classmethod
    def deinit_host(cls):
        host = cls()

        try:
            host.load()
        except NotFound:
            pass

        cls.collection.update({
            '_id': host.id,
        }, {'$set': {
            'status': OFFLINE,
            'ping_timestamp': None,
        }})
