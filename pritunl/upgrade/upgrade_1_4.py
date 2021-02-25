from pritunl.upgrade.utils import get_collection

from pritunl import utils

def upgrade_1_4():
    ip_pool_collection = get_collection('servers_ip_pool')

    docs = ip_pool_collection.find({}, {
        '_id': True,
        'network': True,
    })

    for doc in docs:
        if not doc.get('network'):
            continue

        if isinstance(doc['network'], int):
            continue

        ip_pool_collection.update({
            '_id': doc['_id'],
        }, {'$set': {
            'network': utils.fnv32a(doc['network'])
        }})
