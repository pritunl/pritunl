from pritunl.constants import *
from pritunl.organization import Organization
from pritunl import server
import pritunl.utils as utils

@server.app.route('/organization', methods=['GET'])
def orgs_get():
    orgs = []

    for org in Organization.get_orgs():
        orgs.append({
            'id': org.id,
            'name': org.name
        })

    return utils.jsonify(orgs)
