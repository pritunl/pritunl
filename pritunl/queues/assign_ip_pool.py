from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *
from pritunl import logger
from pritunl import mongo
from pritunl import event
from pritunl import server
from pritunl import queue

import pymongo
import bson

@queue.add_queue
class QueueAssignIpPool(queue.Queue):
    fields = {
        'server_id',
        'network',
        'old_network',
    } | queue.Queue.fields
    type = 'assign_ip_pool'

    def __init__(self, server_id=None,
            network=None, old_network=None, **kwargs):
        queue.Queue.__init__(self, **kwargs)

        if server_id is not None:
            self.server_id = server_id
        if network is not None:
            self.network = network
        if old_network is not None:
            self.old_network = old_network

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
            'network_lock': self.id,
        }})
        if not response['updatedExisting']:
            raise ServerNetworkLocked('Server network is locked', {
                'server_id': self.server_id,
                'queue_id': self.id,
                'queue_type': self.type,
            })

        self.server.ip_pool.assign_ip_pool(self.network)

    def post_task(self):
        try:
            self.server_ip_pool_collection.remove({
                'network': self.old_network,
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
                'network': self.network,
                'server_id': self.server_id,
            })

            self.server_collection.update({
                '_id': self.server_id,
                'network': self.network,
            }, {'$set': {
                'network': self.old_network,
            }})
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
