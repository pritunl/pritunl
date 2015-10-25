from pritunl.helpers import *
from pritunl import mongo
from pritunl import task

class TaskCleanNetworkLinks(task.Task):
    type = 'clean_network_links'

    @cached_static_property
    def user_collection(cls):
        return mongo.get_collection('users')

    @cached_static_property
    def user_net_link_collection(cls):
        return mongo.get_collection('users_net_link')

    def task(self):
        user_ids_link = set(self.user_net_link_collection.find({}, {
            '_id': True,
            'user_id': True,
        }).distinct('user_id'))

        user_ids = set(self.user_collection.find({}, {
            '_id': True,
        }).distinct('_id'))

        self.user_net_link_collection.remove({
            'user_id': {'$in': list(user_ids_link - user_ids)},
        })

task.add_task(TaskCleanNetworkLinks, hours=5, minutes=47)
