from pritunl.helpers import *
from pritunl import mongo
from pritunl import task

class TaskCleanVxlans(task.Task):
    type = 'clean_vxlan'

    @cached_static_property
    def server_collection(cls):
        return mongo.get_collection('servers')

    @cached_static_property
    def vxlan_collection(cls):
        return mongo.get_collection('vxlans')

    def task(self):
        server_ids = set(self.server_collection.find().distinct('_id'))
        vxlan_ids = set(self.vxlan_collection.find().distinct('server_id'))

        self.vxlan_collection.remove({
            'server_id': {'$in': list(vxlan_ids - server_ids)}
        })

task.add_task(TaskCleanVxlans, minutes=52)
