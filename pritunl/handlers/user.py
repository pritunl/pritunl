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

    for i in xrange(2):
        users = []
        cur_page = 0
        user_count = 0
        for user in org.iter_users():
            if page is not None:
                cur_page = user_count / USER_PAGE_COUNT
                if user.type == CERT_CLIENT:
                    user_count += 1
                    if cur_page > page:
                        break
                if cur_page != page:
                    continue

            is_client = user.id in clients
            user_dict = user.dict()
            user_dict['status'] = True if is_client else False
            user_dict['otp_auth'] = otp_auth
            user_dict['servers'] = clients[user.id] if is_client else {}
            users.append(user_dict)

        page_total = user_count / USER_PAGE_COUNT
        if page > page_total:
            page = page_total
            continue
        else:
            break

    if page is not None:
        if user_count and not user_count % USER_PAGE_COUNT:
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
