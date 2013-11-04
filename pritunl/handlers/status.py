from pritunl.constants import *
import pritunl.utils as utils
from pritunl.organization import Organization
from pritunl.server import Server
from pritunl import app_server, __version__

@app_server.app.route('/status', methods=['GET'])
@app_server.auth
def status_get():
    orgs = Organization.get_orgs()
    orgs_count = len(orgs)

    servers_count = 0
    servers_online_count = 0
    clients_count = 0
    for server in Server.get_servers():
        servers_count += 1
        if server.status:
            servers_online_count += 1
        clients_count += len(server.get_clients())

    users_count = 0
    for org in orgs:
        for user in org.get_users():
            if user.type != CERT_CLIENT:
                continue
            users_count += 1

    if not app_server.public_ip:
        app_server.load_public_ip()

    return utils.jsonify({
        'orgs_available': orgs_count,
        'orgs_total': orgs_count,
        'users_online': clients_count,
        'users_total': users_count,
        'servers_online': servers_online_count,
        'servers_total': servers_count,
        'server_version': __version__,
        'public_ip': app_server.public_ip,
    })
