from pritunl.helpers import *
from pritunl import mongo
from pritunl import task

class TaskCleanIpPool(task.Task):
    type = 'clean_ip_pool'

    @cached_static_property
    def pool_collection(cls):
        return mongo.get_collection('servers_ip_pool')

    @cached_static_property
    def server_collection(cls):
        return mongo.get_collection('servers')

    def task(self):
        server_ids = self.server_collection.find({}, {
            '_id': True,
        }).distinct('_id')

        self.pool_collection.remove({
            'server_id': {'$nin': server_ids},
        })

        response = self.pool_collection.aggregate([
            {'$match': {
                'user_id': {'$exists': True},
            }},
            {'$group': {
                '_id': {
                    'network': '$network',
                    'user_id': '$user_id',
                },
                'docs': {'$addToSet': '$_id'},
                'count': {'$sum': 1},
            }},
            {'$match': {
                'count': {'$gt': 1},
            }},
        ])

        for doc in response:
            user_id = doc['_id']['user_id']
            network = doc['_id']['network']
            doc_ids = doc['docs'][1:]

            for doc_id in doc_ids:
                self.pool_collection.update({
                    '_id': doc_id,
                    'network': network,
                    'user_id': user_id,
                }, {'$unset': {
                    'org_id': '',
                    'user_id': '',
                }})

        response = self.pool_collection.aggregate([
            {'$match': {
                'user_id': {'$exists': True},
            }},
            {'$lookup': {
                'from': mongo.prefix + 'users',
                'localField': 'user_id',
                'foreignField': '_id',
                'as': 'user_docs',
            }},
            {'$match': {
                'user_docs': {'$size': 0},
            }},
        ])

        for doc in response:
            self.pool_collection.update({
                '_id': doc['_id'],
                'org_id': doc['org_id'],
                'user_id': doc['user_id'],
            }, {'$unset': {
                'org_id': '',
                'user_id': '',
            }})

task.add_task(TaskCleanIpPool, hours=5, minutes=23)
