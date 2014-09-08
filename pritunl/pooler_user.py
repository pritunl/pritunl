from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.cache import cache_db
from pritunl.organization import Organization
from pritunl.least_common_counter import LeastCommonCounter
from pritunl import app_server
import pritunl.mongo as mongo
import logging
import time
import threading
import uuid
import subprocess
import os
import itertools
import collections

logger = logging.getLogger(APP_NAME)

class PoolerUser(object):
    def __init__(self, org=None):
        self.org_id = org.id

    @static_property
    def collection(cls):
        return mongo.get_collection('users')

    @static_property
    def org_collection(cls):
        return mongo.get_collection('organizations')

    def claim_user(self, name=None, email=None, type=None, disabled=None):
        doc_update = {
            'type': CERT_CLIENT,
        }

        if name is not None:
            doc_update['name'] = name
        if email is not None:
            doc_update['email'] = email
        if type is not None:
            doc_update['type'] = type
        if disabled is not None:
            doc_update['disabled'] = disabled

        doc = self.collection.find_and_modify({
            'org_id': self.org_id,
            'type': CERT_CLIENT_POOL,
        }, doc_update)

        if doc:
            return doc

    @classmethod
    def fill_pool(cls):
        orgs_count = LeastCommonCounter()

        org_ids = cls.org_collection.find({}, {
            '_id': True,
        }).distinct('_id')

        for org_id in org_ids:
            orgs_count[str(org_id)] = 0

        pools = cls.collection.aggregate([
            {'$match': {
                'type': CERT_CLIENT_POOL,
            }},
            {'$project': {
                'org_id': 1,
            }},
            {'$group': {
                '_id': '$org_id',
                'count': {'$sum': 1},
            }},
        ])

        for pool in pools['result']:
            orgs_count[pool['_id']] += pool['count']

        for org_id, count in orgs_count.least_common():
            if count >= USER_POOL_SIZE:
                break

            org = Organization.get_org(id=org_id)
            for _ in xrange(USER_POOL_SIZE - count):
                user = org.new_user(type=CERT_CLIENT_POOL)
                user.commit()
