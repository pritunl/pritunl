from pritunl.constants import *
import pritunl.utils as utils
from pritunl.organization import Organization
from pritunl.server import Server
from pritunl import app_server, __version__

@app_server.app.route('/status', methods=['GET'])
@app_server.auth
def status_get():
    orgs_count = 0
    servers_count = 0
    servers_online_count = 0
    clients_count = 0

    for server in Server.iter_servers():
        servers_count += 1
        if server.status:
            servers_online_count += 1
        clients_count += len(server.clients)

    user_count = 0
    for org in Organization.iter_orgs():
        orgs_count += 1
        user_count += org.user_count

    if not app_server.public_ip:
        app_server.load_public_ip()

    local_networks = utils.get_local_networks()

    return utils.jsonify({
        'org_count': orgs_count,
        'users_online': clients_count,
        'user_count': user_count,
        'servers_online': servers_online_count,
        'server_count': servers_count,
        'server_version': __version__,
        'public_ip': app_server.public_ip,
        'local_networks': local_networks,
    })
