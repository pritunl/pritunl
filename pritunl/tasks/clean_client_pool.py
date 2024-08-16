from pritunl.helpers import *
from pritunl import mongo
from pritunl import task
from pritunl import utils
from pritunl import settings

import datetime

class TaskCleanClientPool(task.Task):
    type = 'clean_client_pool'

    @cached_static_property
    def pool_collection(cls):
        return mongo.get_collection('clients_pool')

    def task(self):
        timestamp_spec = utils.now() - datetime.timedelta(
            seconds=settings.vpn.client_ttl + 10)

        docs = self.pool_collection.find({
            'timestamp': {'$lt': timestamp_spec},
        })

        for doc in docs:
            if doc.get('static'):
                self.pool_collection.delete_one({
                    '_id': doc['_id'],
                    'timestamp': doc['timestamp'],
                })
            else:
                self.pool_collection.update_one({
                    '_id': doc['_id'],
                    'timestamp': doc['timestamp'],
                }, {'$set': {
                    'user_id': None,
                    'mac_addr': None,
                    'client_id': None,
                    'timestamp': None,
                }})

task.add_task(TaskCleanClientPool, minutes=range(0, 60, 5))
