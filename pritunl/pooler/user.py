from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
from pritunl.settings import settings
from pritunl.cache import cache_db
from pritunl.least_common_counter import LeastCommonCounter
from pritunl.app_server import app_server
import pritunl.mongo as mongo
from pritunl import utils
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
    @cached_static_property
    def collection(cls):
        return mongo.get_collection('users')

    @cached_static_property
    def org_collection(cls):
        return mongo.get_collection('organizations')

    @cached_static_property
    def queue_collection(cls):
        return mongo.get_collection('queue')

    @classmethod
    def fill_new_org_pool(cls, org):
        user_types = utils.roundrobin(
            [CERT_CLIENT_POOL] * settings.app.user_pool_size,
            [CERT_SERVER_POOL] * settings.app.server_user_pool_size,
        )

        for user_type in user_types:
            org.new_user(type=user_type, block=False)

    @classmethod
    def fill_pool(cls):
        from pritunl.organization import Organization

        orgs = {}
        orgs_count = LeastCommonCounter()
        type_to_size = {
            CERT_CLIENT_POOL: settings.app.user_pool_size,
            CERT_SERVER_POOL: settings.app.server_user_pool_size,
        }

        for org in Organization.iter_orgs(type=None):
            orgs[org.id] = org
            orgs_count[str(org.id), CERT_CLIENT_POOL] = 0
            orgs_count[str(org.id), CERT_SERVER_POOL] = 0

        pools = cls.collection.aggregate([
            {'$match': {
                'type': {'$in': (CERT_CLIENT_POOL, CERT_SERVER_POOL)},
            }},
            {'$project': {
                'org_id': True,
                'type': True,
            }},
            {'$group': {
                '_id': {
                    'org_id': '$org_id',
                    'type': '$type',
                },
                'count': {'$sum': 1},
            }},
        ])['result']

        for pool in pools:
            orgs_count[pool['_id']['org_id'], pool['_id']['type']] += pool[
                'count']

        pools = cls.queue_collection.aggregate([
            {'$match': {
                'type': 'init_user_pooled',
                'user_doc.type': {'$in': (CERT_CLIENT_POOL, CERT_SERVER_POOL)},
            }},
            {'$project': {
                'user_doc.org_id': True,
                'user_doc.type': True,
            }},
            {'$group': {
                '_id': {
                    'org_id': '$user_doc.org_id',
                    'type': '$user_doc.type',
                },
                'count': {'$sum': 1},
            }},
        ])['result']

        for pool in pools:
            orgs_count[pool['_id']['org_id'], pool['_id']['type']] += pool[
                'count']

        new_users = []

        for org_id_user_type, count in orgs_count.least_common():
            org_id, user_type = org_id_user_type
            pool_size = type_to_size[user_type]

            if count >= pool_size:
                break

            org = orgs[org_id]
            new_users.append([(org, user_type)] * (pool_size - count))

        for org, user_type in utils.roundrobin(*new_users):
            org.new_user(type=user_type, block=False)
