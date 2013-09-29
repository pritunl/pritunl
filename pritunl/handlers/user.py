from pritunl.constants import *
from pritunl.organization import Organization
import pritunl.utils as utils
from pritunl import app_server
import os
import flask

@app_server.app.route('/user/<org_id>', methods=['GET'])
@app_server.auth
def user_get(org_id):
    org = Organization(org_id)
    org_servers = org.get_servers()
    users = []
    users_dict = {}
    users_sort = []
    org_clients = []

    for server in org_servers:
        org_clients += server.get_clients()

    for user in org.get_users():
        name_id = '%s_%s' % (user.name, user.id)
        users_sort.append(name_id)
        users_dict[name_id] = {
            'id': user.id,
            'organization': org.id,
            'name': user.name,
            'type': user.type,
            'status': True if user.id in org_clients else False,
        }

    for name_id in sorted(users_sort):
        users.append(users_dict[name_id])

    return utils.jsonify(users)

@app_server.app.route('/user/<org_id>', methods=['POST'])
@app_server.auth
def user_post(org_id):
    org = Organization(org_id)
    name = flask.request.json['name'].encode()
    name = ''.join(x for x in name if x.isalnum() or x in NAME_SAFE_CHARS)
    user = org.new_user(CERT_CLIENT, name)

    return utils.jsonify({
        'id': user.id,
        'organization': org.id,
        'name': user.name,
        'type': user.type,
        'status': False,
    })

@app_server.app.route('/user/<org_id>/<user_id>', methods=['PUT'])
@app_server.auth
def user_put(org_id, user_id):
    org = Organization(org_id)
    user = org.get_user(user_id)
    name = flask.request.json['name'].encode()
    name = ''.join(x for x in name if x.isalnum() or x in NAME_SAFE_CHARS)
    user.rename(name)
    return utils.jsonify({})

@app_server.app.route('/user/<org_id>/<user_id>', methods=['DELETE'])
@app_server.auth
def user_delete(org_id, user_id):
    org = Organization(org_id)
    user = org.get_user(user_id)
    user.remove()
    return utils.jsonify({})

@app_server.app.route('/user/<org_id>/<user_id>.tar', methods=['GET'])
@app_server.auth
def user_key_archive_get(org_id, user_id):
    org = Organization(org_id)
    user = org.get_user(user_id)
    archive_temp_path = user.build_key_archive()

    with open(archive_temp_path, 'r') as archive_file:
        response = flask.Response(response=archive_file.read(),
            mimetype='application/x-tar')
        response.headers.add('Content-Disposition',
            'inline; filename="%s.tar"' % user.name)

    os.remove(archive_temp_path)
    return response
