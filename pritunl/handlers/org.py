from pritunl.constants import *
from pritunl.organization import Organization
import pritunl.utils as utils
from pritunl import server
import flask

@server.app.route('/organization', methods=['GET'])
def org_get():
    orgs = []

    for org in Organization.get_orgs():
        orgs.append({
            'id': org.id,
            'name': org.name
        })

    return utils.jsonify(orgs)

@server.app.route('/organization', methods=['POST'])
def org_post():
    name = flask.request.json['name'].encode()
    org = Organization(name=name)

    return utils.jsonify({
        'id': org.id,
        'name': org.name
    })
