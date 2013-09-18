from pritunl.constants import *
from pritunl.organization import Organization
from pritunl import server
import pritunl.utils as utils

@server.app.route('/user/<org_id>', methods=['GET'])
def user_get(org_id):
    org = Organization(org_id)
    users = []

    for user in org.get_users():
        users.append({
            'id': user.id,
            'name': user.name,
            'status': False
        })

    return utils.jsonify(users)
