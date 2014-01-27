from pritunl.constants import *
from pritunl.organization import Organization
import pritunl.utils as utils
from pritunl import app_server
import flask
import math
import time

@app_server.app.route('/user/<org_id>', methods=['GET'])
@app_server.app.route('/user/<org_id>/<int:page>', methods=['GET'])
@app_server.auth
def user_get(org_id, page=None):
    page = flask.request.args.get('page', None)
    page = int(page) if page else page
    search = flask.request.args.get('search', None)
    limit = int(flask.request.args.get('limit', USER_PAGE_COUNT))
    org = Organization.get_org(id=org_id)
    otp_auth = False
    search_more = True
    clients = {}

    for server in org.iter_servers():
        if server.otp_auth:
            otp_auth = True
        server_clients = server.clients
        for client_id in server_clients:
            client = server_clients[client_id]
            if client_id not in clients:
                clients[client_id] = {}
            clients[client_id][server.id] = client

    users = []
    for user in org.iter_users(page=page, prefix=search, prefix_limit=limit):
        if user is None:
            search_more = False
            break
        is_client = user.id in clients
        user_dict = user.dict()
        user_dict['status'] = True if is_client else False
        user_dict['otp_auth'] = otp_auth
        user_dict['servers'] = clients[user.id] if is_client else {}
        users.append(user_dict)

    if page is not None:
        return utils.jsonify({
            'page': page,
            'page_total': org.page_total,
            'users': users,
        })
    elif search is not None:
        return utils.jsonify({
            'search': search,
            'search_more': search_more,
            'search_limit': limit,
            'search_count': org.get_last_prefix_count(),
            'search_time':  round((time.time() - flask.g.start), 4),
            'users': users,
        })
    else:
        return utils.jsonify(users)

@app_server.app.route('/user/<org_id>', methods=['POST'])
@app_server.auth
def user_post(org_id):
    org = Organization.get_org(id=org_id)
    name = flask.request.json['name']
    name = ''.join(x for x in name if x.isalnum() or x in NAME_SAFE_CHARS)
    user = org.new_user(CERT_CLIENT, name)

    return utils.jsonify(user.dict())

@app_server.app.route('/user/<org_id>/<user_id>', methods=['PUT'])
@app_server.auth
def user_put(org_id, user_id):
    org = Organization.get_org(id=org_id)
    user = org.get_user(user_id)
    name = flask.request.json['name']
    name = ''.join(x for x in name if x.isalnum() or x in NAME_SAFE_CHARS)
    user.rename(name)

    return utils.jsonify(user.dict())

@app_server.app.route('/user/<org_id>/<user_id>', methods=['DELETE'])
@app_server.auth
def user_delete(org_id, user_id):
    org = Organization.get_org(id=org_id)
    user = org.get_user(user_id)
    user_id = user.id
    user.remove()

    for server in org.iter_servers():
        server_clients = server.clients
        if user_id in server_clients:
            server.restart()

    return utils.jsonify({})

@app_server.app.route('/user/<org_id>/<user_id>/otp_secret', methods=['PUT'])
@app_server.auth
def user_otp_secret_put(org_id, user_id):
    org = Organization.get_org(id=org_id)
    user = org.get_user(user_id)
    user.generate_otp_secret()
    return utils.jsonify(user.dict())
