from pritunl.constants import *
from pritunl.organization import Organization
from pritunl import server
import pritunl.utils as utils
import flask

@server.app.route('/user/<org_id>', methods=['GET'])
def user_get(org_id):
    org = Organization(org_id)
    users = []

    for user in org.get_users():
        users.append({
            'id': user.id,
            'organization': org.id,
            'name': user.name,
            'status': False
        })

    return utils.jsonify(users)

@server.app.route('/user/<org_id>', methods=['POST'])
def user_post(org_id):
    org = Organization(org_id)
    name = flask.request.json['name'].encode()
    user = org.new_user(CERT_CLIENT, name)

    return utils.jsonify({
        'id': user.id,
        'organization': org.id,
        'name': user.name,
        'status': False
    })
