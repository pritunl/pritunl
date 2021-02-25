from pritunl.host.usage import HostUsage

from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *
from pritunl import utils
from pritunl import mongo
from pritunl import logger
from pritunl import event
from pritunl import journal

class Host(mongo.MongoObject):
    fields = {
        'name',
        'hostname',
        'ping_timestamp',
        'instance_id',
        'auto_instance_id',
        'status',
        'start_timestamp',
        'version',
        'public_address',
        'public_address6',
        'auto_public_address',
        'auto_public_address6',
        'auto_public_host',
        'auto_public_host6',
        'routed_subnet6',
        'routed_subnet6_wg',
        'proxy_ndp',
        'link_address',
        'sync_address',
        'local_address',
        'local_address6',
        'auto_local_address',
        'auto_local_address6',
        'local_networks',
        'availability_group',
    }
    fields_default = {
        'status': OFFLINE,
        'availability_group': DEFAULT,
    }

    def __init__(self, name=None, **kwargs):
        mongo.MongoObject.__init__(self)
        self.user_count = None
        self.users_online = None
        self._usage = None

        if name is not None:
            self.name = name

        if self.name is None:
            self.name = utils.random_name()

    @cached_static_property
    def collection(cls):
        return mongo.get_collection('hosts')

    @cached_static_property
    def user_collection(cls):
        return mongo.get_collection('users')

    @property
    def usage(self):
        if not self._usage:
            self._usage = HostUsage(self.id)
        elif self._usage.host_id != self.id:
            self._usage = HostUsage(self.id)
        return self._usage

    @property
    def uptime(self):
        if self.status != ONLINE or not self.start_timestamp:
            return
        return max(int((
            utils.now() - self.start_timestamp).total_seconds()), 1)

    @property
    def public_addr(self):
        return self.auto_public_host or self.public_address or \
            self.auto_public_address

    @property
    def public_addr6(self):
        return self.auto_public_host6 or self.public_address6 or \
            self.auto_public_address6

    @property
    def local_addr(self):
        return self.local_address or self.auto_local_address

    @property
    def local_addr6(self):
        return self.local_address6 or self.auto_local_address6

    @property
    def local_iface(self):
        return utils.find_interface_addr(self.local_addr)

    @property
    def link_addr(self):
        return self.link_address or self.auto_public_host or \
            self.public_address or self.auto_public_address

    @property
    def journal_data(self):
        return {
            'host_id': self.id,
            'host_name': self.name,
            'host_public_address': self.public_addr,
            'host_public_address6': self.public_addr6,
            'host_local_address': self.local_addr,
            'host_local_address6': self.local_addr6,
        }

    def dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'hostname': self.hostname,
            'instance_id': None,
            'status': self.status,
            'uptime': self.uptime,
            'version': self.version,
            'user_count': self.user_count,
            'users_online': self.users_online,
            'local_networks': self.local_networks,
            'public_addr': self.public_addr,
            'public_address': self.public_address,
            'public_addr6': self.public_addr6,
            'public_address6': self.public_address6,
            'routed_subnet6': self.routed_subnet6,
            'routed_subnet6_wg': self.routed_subnet6_wg,
            'proxy_ndp': self.proxy_ndp,
            'link_addr': self.link_addr,
            'link_address': self.link_address,
            'sync_address': self.sync_address,
            'local_address': self.local_address,
            'local_addr': self.local_addr,
            'local_address6': self.local_address6,
            'local_addr6': self.local_addr6,
            'availability_group': self.availability_group,
        }

    def iter_servers(self, fields=None):
        from pritunl import server

        spec = {
            'hosts': self.id,
        }
        if fields:
            fields = {key: True for key in fields}

        for doc in server.Server.collection.find(spec, fields):
            yield server.Server(doc=doc, fields=fields)

    def get_link_user(self, org_ids):
        from pritunl import organization

        for org_id in org_ids:
            org = organization.get_by_id(org_id)
            if not org:
                continue

            usr = org.find_user(resource_id=self.id)
            if not usr:
                logger.info('Creating host link user', 'host',
                    host_id=self.id,
                )

                usr = org.new_user(name=HOST_USER_PREFIX + str(self.id),
                    type=CERT_SERVER, resource_id=self.id)

                journal.entry(
                    journal.USER_CREATE,
                    usr.journal_data,
                    event_long='User created for host linking',
                )

                usr.audit_event('user_created',
                    'User created for host linking')

            return usr

        raise ValueError('No orgs exists in link server')

    def remove_link_user(self):
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
