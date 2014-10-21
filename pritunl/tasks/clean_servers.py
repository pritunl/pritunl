from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *
from pritunl import mongo
from pritunl import task
from pritunl import logger

import time

class TaskCleanServers(task.Task):
    type = 'clean_server'

    @cached_static_property
    def user_collection(cls):
        return mongo.get_collection('users')

    @cached_static_property
    def org_collection(cls):
        return mongo.get_collection('organizations')

    @cached_static_property
    def host_collection(cls):
        return mongo.get_collection('hosts')

    @cached_static_property
    def server_collection(cls):
        return mongo.get_collection('servers')

    def task(self):
        user_ids = set()
        org_ids = set()
        server_ids = set()
        for collection, distinct_set in (
                    (self.user_collection, user_ids),
                    (self.org_collection, org_ids),
                    (self.server_collection, server_ids),
                ):
            for doc_id in collection.find().distinct('_id'):
                distinct_set.add(str(doc_id))
        host_ids = set(self.host_collection.find().distinct('_id'))

        project = {
            '_id': True,
            'primary_user': True,
            'primary_organization': True,
            'organizations': True,
            'hosts': True,
            'links': True,
        }

        for doc in self.server_collection.find({}, project):
            if (doc['primary_user'] or doc['primary_organization']) and (
                    doc['primary_user'] not in user_ids or \
                    doc['primary_organization'] not in org_ids):
                self.server_collection.update({
                    '_id': doc['_id'],
                    'primary_user': doc['primary_user'],
                    'primary_organization': doc['primary_organization'],
                }, {'$set': {
                    'primary_user': None,
                    'primary_organization': None,
                }})

            for item_type, item_distinct in (
                        ('organizations', org_ids),
                        ('hosts', host_ids),
                    ):
                missing_items = []
                for item_id in doc[item_type]:
                    if item_id not in item_distinct:
                        missing_items.append(item_id)
                    if missing_items:
                        self.server_collection.update({
                            '_id': doc['_id'],
                        }, {'$pull': {
                            item_type: {'$in': missing_items},
                        }})

task.add_task(TaskCleanServers, hours=5, minutes=27)
