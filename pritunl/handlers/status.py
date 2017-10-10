from pritunl.constants import *
from pritunl import utils
from pritunl import settings
from pritunl import organization
from pritunl import app
from pritunl import auth
from pritunl import mongo
from pritunl import __version__

@app.app.route('/status', methods=['GET'])
@auth.session_auth
def status_get():
    if settings.app.demo_mode:
        resp = utils.demo_get_cache()
        if resp:
            return utils.jsonify(resp)

    server_collection = mongo.get_collection('servers')
    clients_collection = mongo.get_collection('clients')
    host_collection = mongo.get_collection('hosts')
    org_collection = mongo.get_collection('organizations')

    users_online = len(clients_collection.distinct("user_id", {
        'type': CERT_CLIENT,
    }))

    response = server_collection.aggregate([
        {'$project': {
            '_id': True,
            'status': True,
        }},
        {'$group': {
            '_id': None,
            'server_count': {'$sum': 1},
            'servers_online': {'$sum': {'$cond': {
                'if': {'$eq': ['$status', ONLINE]},
                'then': 1,
                'else': 0,
            }}},
            'servers': {
                '$push': '$status',
            },
        }},
    ])

    val = None
    for val in response:
        break

    if val:
        server_count = val['server_count']
        servers_online = val['servers_online']
    else:
        server_count = 0
        servers_online = 0

    response = host_collection.aggregate([
        {'$project': {
            '_id': True,
            'status': True,
            'local_networks': True,
        }},
        {'$group': {
            '_id': None,
            'host_count': {'$sum': 1},
            'hosts_online': {'$sum': {'$cond': {
                'if': {'$eq': ['$status', ONLINE]},
                'then': 1,
                'else': 0,
            }}},
            'servers': {
                '$push': '$status',
            },
            'local_networks': {'$push':'$local_networks'},
        }},
    ])

    val = None
    for val in response:
        break

    local_networks = set()
    if val:
        host_count = val['host_count']
        hosts_online = val['hosts_online']

        for hst_networks in val['local_networks']:
            for network in hst_networks:
                local_networks.add(network)
    else:
        host_count = 0
        hosts_online = 0

    user_count = organization.get_user_count_multi()

    orgs_count = org_collection.find({
       'type': ORG_DEFAULT,
    }, {
        '_id': True,
    }).count()

    notification = settings.local.notification

    resp = {
        'org_count': orgs_count,
        'users_online': users_online,
        'user_count': user_count,
        'servers_online': servers_online,
        'server_count': server_count,
        'hosts_online': hosts_online,
        'host_count': host_count,
        'server_version': __version__,
        'current_host': settings.local.host_id,
        'public_ip': settings.local.public_ip,
        'local_networks': list(local_networks),
        'notification': notification,
    }
    if settings.app.demo_mode:
        utils.demo_set_cache(resp)
    return utils.jsonify(resp)
