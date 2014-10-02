from pritunl.least_common_counter import LeastCommonCounter

from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
from pritunl.settings import settings
from pritunl.cache import cache_db
from pritunl.app_server import app_server
from pritunl import pooler
from pritunl import mongo
from pritunl import utils
from pritunl import logger

import time
import threading
import uuid
import subprocess
import os
import itertools
import collections

def collection():
    return mongo.get_collection('organizations')

def queue_collection():
    return mongo.get_collection('queue')

@pooler.add_pooler('org')
def fill_org():
    from pritunl.organization import Organization

    org_pool_count = collection.find({
        'type': ORG_POOL,
    }, {
        '_id': True,
    }).count()

    org_pool_count += queue_collection.find({
        'type': 'init_org_pooled',
    }, {
        '_id': True,
    }).count()

    for _ in xrange(settings.app.org_pool_size - org_pool_count):
        org = Organization.new_org(type=ORG_POOL, block=False)
