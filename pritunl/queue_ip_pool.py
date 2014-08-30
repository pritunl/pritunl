from constants import *
from exceptions import *
from descriptors import *
from queue import Queue
from queue import queue_types
from mongo_object import MongoObject
import mongo
import pymongo
import logging
import bson

logger = logging.getLogger(APP_NAME)

class QueueIpPool(Queue):
    fields = {
        'server_id',
        'network',
        'old_network',
    } | Queue.fields

    def __init__(self, server_id=None,
            network=None, old_network=None, **kwargs):
        Queue.__init__(self, **kwargs)
        self.queue_type = 'ip_pool'

        if server_id is not None:
            self.server_id = server_id
        if network is not None:
            self.network = network
        if old_network is not None:
            self.old_network = old_network

    def task(self):
        from server import Server
        server = Server.get_server(id=self.server_id)
        if not server:
            return

        response = server.collection.update({
            '_id': bson.ObjectId(server.id),
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
                'server_id': server.id,
                'queue_id': self.id,
                'queue_type': self.queue_type,
            })

        server.ip_pool.assign_ip_pool(self.network)

    def post_task(self):
        from server import Server
        server = Server.get_server(id=self.server_id)
        if not server:
            return

        server.ip_pool.collection.remove({
            'network': self.old_network,
            'server_id': self.server_id,
        })

        server.collection.update({
            '_id': bson.ObjectId(server.id),
            'network_lock': self.id,
        }, {'$unset': {
            'network_lock': '',
        }})

    def rollback_task(self):
        from server import Server
        server = Server.get_server(id=self.server_id)
        if not server:
            return

        server.ip_pool.collection.remove({
            'network': self.network,
            'server_id': self.server_id,
        })

        server.collection.update({
            '_id': bson.ObjectId(server.id),
            'network': self.network,
        }, {'$set': {
            'network': self.old_network,
        }})

        server.collection.update({
            '_id': bson.ObjectId(server.id),
            'network_lock': self.id,
        }, {'$unset': {
            'network_lock': '',
        }})

queue_types['ip_pool'] = QueueIpPool
