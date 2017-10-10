from pritunl.helpers import *
from pritunl import mongo
from pritunl import task

import time

class TaskCleanUsers(task.Task):
    type = 'clean_users'
    ttl = 300

    @cached_static_property
    def user_collection(cls):
        return mongo.get_collection('users')

    @cached_static_property
    def org_collection(cls):
        return mongo.get_collection('organizations')

    def _get_org_ids(self):
        return set(self.org_collection.find({}, {
            '_id': True,
        }).distinct('_id'))

    def _get_user_org_ids(self):
        return set(self.user_collection.find({}, {
            '_id': True,
            'org_id': True,
        }).distinct('org_id'))

    def task(self):
        # Remove users from orgs that dont exists check twice to reduce
        # possibility of deleting a ca user durning org creation
        user_org_ids = self._get_user_org_ids()
        time.sleep(60)
        user_org_ids &= self._get_user_org_ids()

        org_ids = self._get_org_ids()

        self.user_collection.remove({
            'org_id': {'$in': list(user_org_ids - org_ids)},
        })

task.add_task(TaskCleanUsers, hours=5, minutes=17)
