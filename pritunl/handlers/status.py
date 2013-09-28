from pritunl.constants import *
import pritunl.utils as utils
from pritunl.organization import Organization
from pritunl.server import Server
from pritunl import app_server

@app_server.app.route('/status', methods=['GET'])
def status_get():
    orgs = Organization.get_orgs()
    orgs_count = len(orgs)

    clients_count = 0
    for server in Server.get_servers():
        clients_count += len(server.get_clients())

    users_count = 0
    for org in orgs:
        users_count += org.count_users()

    return utils.jsonify({
        'orgs_available': orgs_count,
        'orgs_total': orgs_count,
        'users_online': clients_count,
        'users_total': users_count,
        'servers_online': 4,
        'servers_total': 4,
        'public_ip': app_server.public_ip,
    })
