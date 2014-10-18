from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *
from pritunl import settings
from pritunl import pooler
from pritunl import logger
from pritunl import mongo
from pritunl import utils
from pritunl import queue

@pooler.add_pooler('dh_params')
def fill_dh_params():
    collection = mongo.get_collection('dh_params')
    queue_collection = mongo.get_collection('queue')

    dh_param_bits_pool = settings.app.dh_param_bits_pool
    if len(dh_param_bits_pool) > 1:
        dh_param_counts = utils.LeastCommonCounter(
            {x: 0 for x in dh_param_bits_pool})

        pools = collection.aggregate([
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

        pools = queue_collection.aggregate([
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
        dh_param_counts = utils.LeastCommonCounter()

        pool_count = collection.find({
            'dh_param_bits': dh_param_bits_pool[0],
        }, {
            '_id': True
        }).count()

        dh_param_counts[dh_param_bits_pool[0]] = pool_count

        pool_count = queue_collection.find({
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
        que = queue.start('dh_params', dh_param_bits=dh_param_bits,
            priority=LOW)
        logger.debug('Queue dh params', 'server',
            queue_id=que.id,
            dh_param_bits=dh_param_bits,
        )
