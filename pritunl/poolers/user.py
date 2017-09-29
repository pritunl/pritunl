from pritunl.constants import *
from pritunl import settings
from pritunl import pooler
from pritunl import mongo
from pritunl import utils
from pritunl import organization

@pooler.add_pooler('user')
def fill_user():
    collection = mongo.get_collection('users')
    queue_collection = mongo.get_collection('queue')

    orgs = {}
    orgs_count = utils.LeastCommonCounter()
    type_to_size = {
        CERT_CLIENT_POOL: settings.app.user_pool_size,
        CERT_SERVER_POOL: settings.app.server_user_pool_size,
    }

    for org in organization.iter_orgs(type=None):
        orgs[org.id] = org
        orgs_count[org.id, CERT_CLIENT_POOL] = 0
        orgs_count[org.id, CERT_SERVER_POOL] = 0

    pools = collection.aggregate([
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
    ])

    for pool in pools:
        orgs_count[pool['_id']['org_id'], pool['_id']['type']] += pool[
            'count']

    pools = queue_collection.aggregate([
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
    ])

    for pool in pools:
        orgs_count[pool['_id']['org_id'], pool['_id']['type']] += pool[
            'count']

    new_users = []

    for org_id_user_type, count in orgs_count.least_common():
        org_id, user_type = org_id_user_type
        pool_size = type_to_size[user_type]

        if count >= pool_size:
            break

        org = orgs.get(org_id)
        if not org:
            continue
        new_users.append([(org, user_type)] * (pool_size - count))

    for org, user_type in utils.roundrobin(*new_users):
        org.new_user(type=user_type, block=False)

@pooler.add_pooler('new_user')
def fill_new_user(org):
    user_types = utils.roundrobin(
        [CERT_CLIENT_POOL] * settings.app.user_pool_size,
        [CERT_SERVER_POOL] * settings.app.server_user_pool_size,
    )

    for user_type in user_types:
        org.new_user(type=user_type, block=False)
