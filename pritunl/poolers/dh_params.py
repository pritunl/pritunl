from pritunl.constants import *
from pritunl import settings
from pritunl import pooler
from pritunl import mongo
from pritunl import utils
from pritunl import queue

@pooler.add_pooler('dh_params')
def fill_dh_params():
    collection = mongo.get_collection('dh_params')
    queue_collection = mongo.get_collection('queue')

    new_dh_params = []
    dh_param_bits_pool = settings.app.dh_param_bits_pool
    dh_param_counts = utils.LeastCommonCounter()

    for dh_param_bits in dh_param_bits_pool:
        pool_count = collection.find({
            'dh_param_bits': dh_param_bits,
        }, {
            '_id': True
        }).count()

        dh_param_counts[dh_param_bits] = pool_count

        pool_count = queue_collection.find({
            'type': 'dh_params',
            'dh_param_bits': dh_param_bits,
        }, {
            '_id': True
        }).count()

        dh_param_counts[dh_param_bits] += pool_count

    for dh_param_bits, count in dh_param_counts.least_common():
        new_dh_params.append([dh_param_bits] * (
            settings.app.server_pool_size - count))

    for dh_param_bits in utils.roundrobin(*new_dh_params):
        que = queue.start('dh_params', dh_param_bits=dh_param_bits,
            priority=LOW)
