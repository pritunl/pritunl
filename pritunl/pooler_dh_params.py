from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
from pritunl.cache import cache_db
from pritunl.least_common_counter import LeastCommonCounter
from pritunl.queue_dh_params import QueueDhParams
from pritunl import app_server
import pritunl.logger as logger
import pritunl.mongo as mongo
import pritunl.utils as utils
import logging
import time
import threading
import uuid
import subprocess
import os
import itertools
import collections

class PoolerDhParams(object):
    @cached_static_property
    def collection(cls):
        return mongo.get_collection('dh_params')

    @classmethod
    def fill_pool(cls):
        from pritunl.organization import Organization

        if len(DH_PARAM_BITS_POOL) > 1:
            dh_param_counts = LeastCommonCounter(
                {x: 0 for x in DH_PARAM_BITS_POOL})

            pools = cls.collection.aggregate([
                {'$match': {
                    'dh_param_bits': {'$in': DH_PARAM_BITS_POOL},
                }},
                {'$project': {
                    'dh_param_bits': True,
                }},
                {'$group': {
                    '_id': '$dh_param_bits',
                    'count': {'$sum': 1},
                }},
            ])['result']

            for pool in pools:
                dh_param_counts[pool['_id']] = pool['count']
        else:
            dh_param_counts = LeastCommonCounter()

            pool_count = cls.collection.find({
                'dh_param_bits': DH_PARAM_BITS_POOL[0],
            }, {
                '_id': True
            }).count()

            dh_param_counts[DH_PARAM_BITS_POOL[0]] = pool_count

        new_dh_params = []

        for dh_param_bits, count in dh_param_counts.least_common():
            new_dh_params.append([dh_param_bits] * (SERVER_POOL_SIZE - count))

        for dh_param_bits in utils.roundrobin(*new_dh_params):
            queue = QueueDhParams(dh_param_bits=dh_param_bits)
            queue.start()
            logger.debug('Queue dh params', 'server',
                queue_id=queue.id,
                dh_param_bits=dh_param_bits,
            )

PoolerDhParams.fill_pool()
