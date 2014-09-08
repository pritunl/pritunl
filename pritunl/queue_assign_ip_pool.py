from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
from pritunl.event import Event
from pritunl.queue import Queue, add_queue
from pritunl.mongo_object import MongoObject
import pritunl.mongo as mongo
import pymongo
import logging
import bson

logger = logging.getLogger(APP_NAME)

class QueueAssignIpPool(Queue):
    fields = {
        'server_id',
        'network',
        'old_network',
    } | Queue.fields
    type = 'assign_ip_pool'

    def __init__(self, server_id=None,
            network=None, old_network=None, **kwargs):
        Queue.__init__(self, **kwargs)

        if server_id is not None:
            self.server_id = server_id
        if network is not None:
            self.network = network
        if old_network is not None:
            self.old_network = old_network

    @cached_property
    def server(self):
        from server import Server
        return Server.get_server(id=self.server_id)

    def task(self):
        if not self.server:
            return

        response = self.server.collection.update({
            '_id': bson.ObjectId(self.server.id),
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
                'server_id': self.server.id,
                'queue_id': self.id,
                'queue_type': self.type,
            })

        self.server.ip_pool.assign_ip_pool(self.network)

    def post_task(self):
        if not self.server:
            return

        self.server.ip_pool.collection.remove({
            'network': self.old_network,
            'server_id': self.server_id,
        })

        self.server.collection.update({
            '_id': bson.ObjectId(self.server_id),
            'network_lock': self.id,
        }, {'$unset': {
            'network_lock': '',
        }})

    def rollback_task(self):
        if not self.server:
            return

        self.server.ip_pool.collection.remove({
            'network': self.network,
            'server_id': self.server_id,
        })

        self.server.collection.update({
            '_id': bson.ObjectId(self.server_id),
            'network': self.network,
        }, {'$set': {
            'network': self.old_network,
        }})

        self.server.collection.update({
            '_id': bson.ObjectId(self.server_id),
            'network_lock': self.id,
        }, {'$unset': {
            'network_lock': '',
        }})

    def complete_task(self):
        for org_id in self.server.organizations:
            Event(type=USERS_UPDATED, resource_id=org_id)

add_queue('assign_ip_pool', QueueAssignIpPool)
