from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
from pritunl.task import Task, add_task
import logging
import time
import mongo

logger = logging.getLogger(APP_NAME)

class TaskCleanUsers(Task):
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

add_task(TaskCleanUsers, hours=5, minutes=17)
