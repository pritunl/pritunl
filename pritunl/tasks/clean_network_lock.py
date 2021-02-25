from pritunl.helpers import *
from pritunl import mongo
from pritunl import task
from pritunl import utils

class TaskCleanNetworkLock(task.Task):
    type = 'clean_network_lock'

    @cached_static_property
    def server_collection(cls):
        return mongo.get_collection('servers')

    def task(self):
        self.server_collection.update_many({
            'network_lock_ttl': {'$lt': utils.now()},
        }, {'$unset': {
            'network_lock': '',
            'network_lock_ttl': '',
        }})

task.add_task(TaskCleanNetworkLock,
    minutes=range(0, 60, 8), run_on_start=True)
