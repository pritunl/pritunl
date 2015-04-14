from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *
from pritunl import utils
from pritunl import settings
from pritunl import server
from pritunl import organization
from pritunl import app
from pritunl import auth
from pritunl import mongo
from pritunl import __version__

@app.app.route('/status', methods=['GET'])
@auth.session_auth
def status_get():
    server_collection = mongo.get_collection('servers')
    host_collection = mongo.get_collection('hosts')
    org_collection = mongo.get_collection('organizations')

    response = server_collection.aggregate([
        {'$project': {
            'client': '$instances.clients',
        }},
        {'$unwind': '$client'},
        {'$unwind': '$client'},
        {'$match': {
            'client.type': CERT_CLIENT,
        }},
        {'$group': {
            '_id': None,
            'clients': {'$addToSet': '$client.id'},
        }},
    ])

    val = None
    for val in response:
        break

    if val:
        users_online = len(val['clients'])
    else:
        users_online = 0

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
        }},
    ])

    val = None
    for val in response:
        break

    if val:
        host_count = val['host_count']
        hosts_online = val['hosts_online']
    else:
        host_count = 0
        hosts_online = 0

    user_count = organization.get_user_count_multi()
    local_networks = utils.get_local_networks()

    orgs_count = org_collection.find({
       'type': ORG_DEFAULT,
    }, {
        '_id': True,
    }).count()

    if settings.local.openssl_heartbleed:
        notification = 'You are running an outdated version of openssl ' + \
            'containting the heartbleed bug. This could allow an attacker ' + \
            'to compromise your server. Please upgrade your openssl ' + \
            'package and restart the pritunl service.'
    else:
        notification = settings.local.notification

    return utils.jsonify({
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
        'local_networks': local_networks,
        'notification': notification,
    })
