from pritunl.constants import *
from pritunl.organization import Organization
import pritunl.utils as utils
from pritunl import app_server
import flask
import math

@app_server.app.route('/user/<org_id>', methods=['GET'])
@app_server.app.route('/user/<org_id>/<int:page>', methods=['GET'])
@app_server.auth
def user_get(org_id, page=None):
    page = flask.request.args.get('page', None)
    page = int(page) if page else page
    org = Organization.get_org(id=org_id)
    otp_auth = False
    users = []
    server_users = []
    users_dict = {}
    users_sort = []
    user_count_total = 0
    clients = {}

    for server in org.get_servers():
        if server.otp_auth:
            otp_auth = True
        server_clients = server.clients
        for client_id in server_clients:
            client = server_clients[client_id]
            if client_id not in clients:
                clients[client_id] = {}
            clients[client_id][server.id] = client

    for user in org.get_users():
        is_client = user.id in clients
        name_id = '%s_%s' % (user.name, user.id)
        users_sort.append(name_id)
        users_dict[name_id] = user.dict()
        users_dict[name_id]['status'] = True if is_client else False
        users_dict[name_id]['otp_auth'] = otp_auth
        users_dict[name_id]['servers'] = clients[user.id] if is_client else {}
        if user.type == CERT_CLIENT:
            user_count_total += 1

    cur_page = 0
    user_count = 0
    page_total = user_count_total / USER_PAGE_COUNT
    page = min(page, page_total)
    for name_id in sorted(users_sort):
        if page is not None:
            cur_page = user_count / USER_PAGE_COUNT
            if users_dict[name_id]['type'] == CERT_CLIENT:
                user_count += 1
                if cur_page > page:
                    break
            if cur_page != page:
                    continue
        users.append(users_dict[name_id])

    if page is not None:
        if user_count_total and not user_count_total % USER_PAGE_COUNT:
            page_total -= 1
        return utils.jsonify({
            'page': page,
            'page_total': page_total,
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

    for server in org.get_servers():
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
