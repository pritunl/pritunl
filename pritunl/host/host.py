from pritunl.host.usage import HostUsage

from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *
from pritunl import settings
from pritunl import utils
from pritunl import mongo
from pritunl import logger
from pritunl import event

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
        'link_address',
    }
    fields_default = {
        'status': OFFLINE,
    }

    def __init__(self, name=None, **kwargs):
        mongo.MongoObject.__init__(self, **kwargs)

        if 'id' not in kwargs and 'doc' not in kwargs and 'spec' not in kwargs:
            self.id = settings.local.host_id

        self.usage = HostUsage(self.id)

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

    @cached_static_property
    def user_collection(cls):
        return mongo.get_collection('users')

    @property
    def uptime(self):
        if not self.start_timestamp:
            return
        return max((utils.now() - self.start_timestamp).seconds, 1)

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
            'link_address': self.link_address,
        }

    def iter_servers(self, fields=None):
        from pritunl import server

        spec = {
            'hosts': self.id,
        }
        if fields:
            fields = {key: True for key in fields}

        for doc in server.Server.collection.find(spec, fields):
            yield server.Server(doc=doc)

    def get_link_user(self, org_id):
        from pritunl import organization

        logger.debug('Creating host link user. %r' % {
            'host_id': self.id,
        })

        org = organization.get_org(id=org_id)
        usr = org.find_user(resource_id=self.id)

        if not usr:
            usr = org.new_user(name=HOST_USER_PREFIX + str(self.id),
                type=CERT_SERVER, resource_id=self.id)

        return usr

    def remove_link_user(self):
        logger.debug('Removing host link user. %r' % {
            'host_id': self.id,
        })

        self.user_collection.remove({
            'resource_id': self.id,
        })

    def remove(self):
        send_event = False

        if self.status == ONLINE:
            raise HostError('Host must be offline to remove')

        for svr in self.iter_servers(('_id', 'replica_count', 'hosts')):
            send_event = True
            svr.remove_host(self.id)
            event.Event(type=SERVER_HOSTS_UPDATED, resource_id=svr.id)

        if send_event:
            event.Event(type=SERVERS_UPDATED)

        self.user_collection.remove({
            'resource_id': self.id,
        })
        mongo.MongoObject.remove(self)
