from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *
from pritunl import mongo
from pritunl import task

import time

class TaskCleanUsers(task.Task):
    type = 'clean_users'

    @cached_static_property
    def collection(cls):
        return mongo.get_collection('users')

    @cached_static_property
    def org_collection(cls):
        return mongo.get_collection('organizations')

    def _get_org_ids(self):
        return set(self.org_collection.find({}, {
            '_id': True,
        }).distinct('_id'))

    def task(self):
        # Remove users from orgs that dont exists check twice to reduce
        # possibility of deleting a ca user durning org creation
        org_ids = self._get_org_ids()
        time.sleep(30)
        org_ids2 = self._get_org_ids()

        self.collection.remove({
            'org_id': {'$nin': list(org_ids & org_ids2)},
        })

task.add_task(TaskCleanUsers, hours=5, minutes=17)
