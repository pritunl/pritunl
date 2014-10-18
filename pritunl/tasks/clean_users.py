from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *
from pritunl import mongo
from pritunl import task
from pritunl import logger

import time

class TaskCleanUsers(task.Task):
    type = 'clean_users'

    @cached_static_property
    def collection(cls):
        return mongo.get_collection('users')

    @cached_static_property
    def org_collection(cls):
        return mongo.get_collection('organizations')

    def task(self):
        # Remove users from orgs that dont exists
        org_ids = self.org_collection.find({}, {
            '_id',
        }).distinct('_id')
        org_ids = [str(x) for x in org_ids]

        self.collection.remove({
            'org_id': {'$nin': org_ids},
        })

task.add_task(TaskCleanUsers, hours=5, minutes=17)
