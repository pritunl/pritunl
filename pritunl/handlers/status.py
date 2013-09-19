from pritunl.constants import *
import pritunl.utils as utils
from pritunl.organization import Organization
from pritunl import server

@server.app.route('/status', methods=['GET'])
def status_get():
    orgs = Organization.get_orgs()
    orgs_count = len(orgs)
    users_count = 0
    for org in orgs:
        users_count += org.count_users()

    return utils.jsonify({
        'orgs_available': orgs_count,
        'orgs_total': orgs_count,
        'users_online': int(users_count / 2),
        'users_total': users_count,
        'servers_online': 4,
        'servers_total': 4,
    })
