from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *
from pritunl import logger
from pritunl import mongo
from pritunl import event
from pritunl import server
from pritunl import queue
from pritunl import utils

import datetime

@queue.add_queue
class QueueAssignIpPool(queue.Queue):
    fields = {
        'server_id',
        'network',
        'network_start',
        'network_end',
        'network_hash',
        'old_network',
        'old_network_start',
        'old_network_end',
        'old_network_hash',
    } | queue.Queue.fields
    type = 'assign_ip_pool'

    def __init__(self, server_id=None,
            network=None, network_start=None, network_end=None,
            network_hash=None, old_network=None, old_network_start=None,
            old_network_end=None, old_network_hash=None, **kwargs):
        queue.Queue.__init__(self, **kwargs)

        if server_id is not None:
            self.server_id = server_id
        if network is not None:
            self.network = network
        if network_start is not None:
            self.network_start = network_start
        if network_end is not None:
            self.network_end = network_end
        if network_hash is not None:
            self.network_hash = network_hash
        if old_network is not None:
            self.old_network = old_network
        if old_network_start is not None:
            self.old_network_start = old_network_start
        if old_network_end is not None:
            self.old_network_end = old_network_end
        if old_network_hash is not None:
            self.old_network_hash = old_network_hash

    @cached_property
    def server(self):
        return server.get_by_id(self.server_id)

    @cached_static_property
    def server_collection(cls):
        return mongo.get_collection('servers')

    @cached_static_property
    def server_ip_pool_collection(cls):
        return mongo.get_collection('servers_ip_pool')

    def task(self):
        if not self.server:
            logger.warning('Tried to run assign_ip_pool task queue ' +
                'but server is no longer available', 'queues',
                server_id=self.server_id,
            )
            return

        response = self.server_collection.update({
            '_id': self.server_id,
            '$or': [
                {'network_lock': self.id},
                {'network_lock': {'$exists': False}},
            ],
        }, {'$set': {
            'network': self.network,
            'network_start': self.network_start,
            'network_end': self.network_end,
            'network_lock': self.id,
            'network_lock_ttl': utils.now() + datetime.timedelta(minutes=3),
        }})
        if not response['updatedExisting']:
            raise ServerNetworkLocked('Server network is locked', {
                'server_id': self.server_id,
                'queue_id': self.id,
                'queue_type': self.type,
            })

        self.server.ip_pool.assign_ip_pool(self.network,
            self.network_start, self.network_end, self.network_hash)

    def post_task(self):
        try:
            self.server_ip_pool_collection.remove({
                'network': self.old_network_hash,
                'server_id': self.server_id,
            })
        finally:
            self.server_collection.update({
                '_id': self.server_id,
                'network_lock': self.id,
            }, {'$unset': {
                'network_lock': '',
            }})

    def rollback_task(self):
        try:
            self.server_ip_pool_collection.remove({
                'network': self.network_hash,
                'server_id': self.server_id,
            })

            doc = {
                'network': self.old_network,
                'network_start': self.old_network_start,
                'network_end': self.old_network_end,
            }

            if not self.old_network_start or not self.old_network_end:
                doc['mode'] = TUNNEL

            self.server_collection.update({
                '_id': self.server_id,
                'network': self.network,
                'network_start': self.network_start,
                'network_end': self.network_end,
            }, {'$set': doc})
        finally:
            self.server_collection.update({
                '_id': self.server_id,
                'network_lock': self.id,
            }, {'$unset': {
                'network_lock': '',
            }})

    def complete_task(self):
        if not self.server:
            logger.warning('Tried to run assign_ip_pool complete queue ' +
                'but server is no longer available', 'queues',
                server_id=self.server_id,
            )
            return

        for org_id in self.server.organizations:
            event.Event(type=USERS_UPDATED, resource_id=org_id)
