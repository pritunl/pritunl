from pritunl.constants import *
from pritunl import utils
from pritunl.settings import settings
from pritunl.organization import Organization
from pritunl.server import Server
from pritunl.app_server import app_server
from pritunl import __version__

@app_server.app.route('/status', methods=['GET'])
@app_server.auth
def status_get():
    orgs_count = 0
    servers_count = 0
    servers_online_count = 0
    clients_count = 0
    clients = set()

    for server in Server.iter_servers():
        servers_count += 1
        if server.status:
            servers_online_count += 1
        # MongoDict doesnt support set(server.clients)
        clients = clients | set(server.clients.keys())
    clients_count = len(clients)

    user_count = Organization.get_user_count_multi()
    local_networks = utils.get_local_networks()

    if settings.local.openssl_heartbleed:
        notification = 'You are running an outdated version of openssl ' + \
            'containting the heartbleed bug. This could allow an attacker ' + \
            'to compromise your server. Please upgrade your openssl ' + \
            'package and restart the pritunl service.'
    else:
        notification = app_server.notification

    return utils.jsonify({
        'org_count': orgs_count,
        'users_online': clients_count,
        'user_count': user_count,
        'servers_online': servers_online_count,
        'server_count': servers_count,
        'server_version': __version__,
        'public_ip': settings.local.public_ip,
        'local_networks': local_networks,
        'notification': notification,
    })
