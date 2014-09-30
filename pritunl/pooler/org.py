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

class PoolerOrg(object):
    @cached_static_property
    def collection(cls):
        return mongo.get_collection('organizations')

    @cached_static_property
    def queue_collection(cls):
        return mongo.get_collection('queue')

    @classmethod
    def fill_pool(cls):
        from pritunl.organization import Organization

        org_pool_count = cls.collection.find({
            'type': ORG_POOL,
        }, {
            '_id': True,
        }).count()

        org_pool_count += cls.queue_collection.find({
            'type': 'init_org_pooled',
        }, {
            '_id': True,
        }).count()

        for _ in xrange(settings.app.org_pool_size - org_pool_count):
            org = Organization.new_org(type=ORG_POOL, block=False)
