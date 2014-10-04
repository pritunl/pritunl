from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
from pritunl import mongo
from pritunl import task
from pritunl import logger

class TaskCleanIpPool(task.Task):
    type = 'clean_ip_pool'

    @cached_static_property
    def collection(cls):
        return mongo.get_collection('servers_ip_pool')

    @cached_static_property
    def server_collection(cls):
        return mongo.get_collection('servers')

    def task(self):
        org_ids = self.server_collection.find({}, {
            '_id',
        }).distinct('_id')
        org_ids = [str(x) for x in org_ids]

        self.collection.remove({
            'server_id': {'$nin': org_ids},
        })

task.add_task(TaskCleanIpPool, hours=5, minutes=23)
