from pritunl.constants import *
from pritunl.organization import Organization
import pritunl.utils as utils
from pritunl import server
import flask

@server.app.route('/user/<org_id>', methods=['GET'])
def user_get(org_id):
    org = Organization(org_id)
    users = []
    users_dict = {}
    users_sort = []

    for user in org.get_users():
        name_id = '%s_%s' % (user.name, user.id)
        users_sort.append(name_id)
        users_dict[name_id] = {
            'id': user.id,
            'organization': org.id,
            'name': user.name,
            'status': False,
        }

    for name_id in sorted(users_sort):
        users.append(users_dict[name_id])

    return utils.jsonify(users)

@server.app.route('/user/<org_id>', methods=['POST'])
def user_post(org_id):
    org = Organization(org_id)
    name = flask.request.json['name'].encode()
    name = ''.join(x for x in name if x.isalnum() or x in NAME_SAFE_CHARS)
    user = org.new_user(CERT_CLIENT, name)

    return utils.jsonify({
        'id': user.id,
        'organization': org.id,
        'name': user.name,
        'status': False,
    })

@server.app.route('/user/<org_id>/<user_id>', methods=['PUT'])
def user_put(org_id, user_id):
    org = Organization(org_id)
    user = org.get_user(user_id)
    name = flask.request.json['name'].encode()
    name = ''.join(x for x in name if x.isalnum() or x in NAME_SAFE_CHARS)
    user.rename(name)
    return utils.jsonify({})

@server.app.route('/user/<org_id>/<user_id>', methods=['DELETE'])
def user_delete(org_id, user_id):
    org = Organization(org_id)
    user = org.get_user(user_id)
    user.remove()
    return utils.jsonify({})
