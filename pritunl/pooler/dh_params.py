from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
from pritunl.settings import settings
from pritunl.cache import cache_db
from pritunl.least_common_counter import LeastCommonCounter
from pritunl.queue_dh_params import QueueDhParams
from pritunl import app_server
import pritunl.logger as logger
import pritunl.mongo as mongo
import pritunl.utils as utils

class PoolerDhParams(object):
    @cached_static_property
    def collection(cls):
        return mongo.get_collection('dh_params')

    @cached_static_property
    def queue_collection(cls):
        return mongo.get_collection('queue')

    @classmethod
    def fill_pool(cls):
        dh_param_bits_pool = settings.app.dh_param_bits_pool
        if len(dh_param_bits_pool) > 1:
            dh_param_counts = LeastCommonCounter(
                {x: 0 for x in dh_param_bits_pool})

            pools = cls.collection.aggregate([
                {'$match': {
                    'dh_param_bits': {'$in': dh_param_bits_pool},
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

            pools = cls.queue_collection.aggregate([
                {'$match': {
                    'type': 'dh_params',
                    'dh_param_bits': {'$in': dh_param_bits_pool},
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
                dh_param_counts[pool['_id']] += pool['count']
        else:
            dh_param_counts = LeastCommonCounter()

            pool_count = cls.collection.find({
                'dh_param_bits': dh_param_bits_pool[0],
            }, {
                '_id': True
            }).count()

            dh_param_counts[dh_param_bits_pool[0]] = pool_count

            pool_count = cls.queue_collection.find({
                'type': 'dh_params',
                'dh_param_bits': dh_param_bits_pool[0],
            }, {
                '_id': True
            }).count()

            dh_param_counts[dh_param_bits_pool[0]] += pool_count

        new_dh_params = []

        for dh_param_bits, count in dh_param_counts.least_common():
            new_dh_params.append([dh_param_bits] * (
                settings.app.server_pool_size - count))

        for dh_param_bits in utils.roundrobin(*new_dh_params):
            queue = QueueDhParams(dh_param_bits=dh_param_bits, priority=LOW)
            queue.start()
            logger.debug('Queue dh params', 'server',
                queue_id=queue.id,
                dh_param_bits=dh_param_bits,
            )
