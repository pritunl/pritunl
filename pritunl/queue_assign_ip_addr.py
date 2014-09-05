from constants import *
from exceptions import *
from descriptors import *
from queue import Queue, add_queue
from event import Event
from mongo_object import MongoObject
import mongo
import pymongo
import logging
import bson

logger = logging.getLogger(APP_NAME)

class QueueAssignIpAddr(Queue):
    fields = {
        'server_id',
        'org_id',
        'user_id',
    } | Queue.fields

    def __init__(self, server_id=None,
            org_id=None, user_id=None, **kwargs):
        Queue.__init__(self, **kwargs)
        self.type = 'assign_ip_addr'

        if server_id is not None:
            self.server_id = server_id
        if org_id is not None:
            self.org_id = org_id
        if user_id is not None:
            self.user_id = user_id

    def task(self):
        from server import Server
        server = Server.get_server(id=self.server_id)
        if not server:
            return

        for i in xrange(5):
            if server.network_lock:
                time.sleep(2)
                server.load()
            else:
                break

        if server.network_lock:
            raise ServerNetworkLocked('Server network is locked', {
                'server_id': server.id,
                'queue_id': self.id,
                'queue_type': self.type,
            })

        server.ip_pool.assign_ip_addr(self.org_id, self.user_id)

    def complete_task(self):
        Event(type=USERS_UPDATED, resource_id=self.org_id)

add_queue('assign_ip_addr', QueueAssignIpAddr)
