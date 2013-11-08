from pritunl.constants import *
from pritunl.organization import Organization
import pritunl.utils as utils
from pritunl import app_server
import flask

@app_server.app.route('/user/<org_id>', methods=['GET'])
@app_server.auth
def user_get(org_id):
    org = Organization(org_id)
    otp_auth = False
    users = []
    users_dict = {}
    users_sort = []
    clients = {}

    for server in org.get_servers():
        if server.otp_auth:
            otp_auth = True
        server_clients = server.get_clients()
        for client_id in server_clients:
            client = server_clients[client_id]
            if client_id not in clients:
                clients[client_id] = {}
            clients[client_id][server.id] = client

    for user in org.get_users():
        name_id = '%s_%s' % (user.name, user.id)
        users_sort.append(name_id)
        users_dict[name_id] = {
            'id': user.id,
            'organization': org.id,
            'name': user.name,
            'type': user.type,
            'status': True if user.id in clients else False,
            'otp_auth': otp_auth,
            'otp_secret': user.otp_secret,
            'servers': clients[user.id] if user.id in clients else {},
        }

    for name_id in sorted(users_sort):
        users.append(users_dict[name_id])

    return utils.jsonify(users)

@app_server.app.route('/user/<org_id>', methods=['POST'])
@app_server.auth
def user_post(org_id):
    org = Organization(org_id)
    name = flask.request.json['name']
    name = ''.join(x for x in name if x.isalnum() or x in NAME_SAFE_CHARS)
    user = org.new_user(CERT_CLIENT, name)

    return utils.jsonify({})

@app_server.app.route('/user/<org_id>/<user_id>', methods=['PUT'])
@app_server.auth
def user_put(org_id, user_id):
    org = Organization(org_id)
    user = org.get_user(user_id)
    name = flask.request.json['name']
    name = ''.join(x for x in name if x.isalnum() or x in NAME_SAFE_CHARS)
    user.rename(name)
    return utils.jsonify({})

@app_server.app.route('/user/<org_id>/<user_id>', methods=['DELETE'])
@app_server.auth
def user_delete(org_id, user_id):
    org = Organization(org_id)
    user = org.get_user(user_id)
    user_id = user.id
    user.remove()
    for server in org.get_servers():
        server_clients = server.get_clients()
        if user_id in server_clients:
            server.restart()
    return utils.jsonify({})

@app_server.app.route('/user/<org_id>/<user_id>/otp_secret',
    methods=['DELETE'])
@app_server.auth
def user_otp_secret_delete(org_id, user_id):
    org = Organization(org_id)
    user = org.get_user(user_id)
    user.generate_otp_secret()
    return utils.jsonify({})
