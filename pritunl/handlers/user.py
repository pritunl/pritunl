from pritunl.constants import *
from pritunl.organization import Organization
import pritunl.utils as utils
from pritunl import app_server
import flask
import math
import time

@app_server.app.route('/user/<org_id>', methods=['GET'])
@app_server.app.route('/user/<org_id>/<user_id>', methods=['GET'])
@app_server.app.route('/user/<org_id>/<int:page>', methods=['GET'])
@app_server.auth
def user_get(org_id, user_id=None, page=None):
    org = Organization.get_org(id=org_id)
    if user_id:
        return utils.jsonify(org.get_user(user_id).dict())
    else:
        page = flask.request.args.get('page', None)
        page = int(page) if page else page
        search = flask.request.args.get('search', None)
        limit = int(flask.request.args.get('limit', USER_PAGE_COUNT))
        otp_auth = False
        search_more = True
        server_count = 0
        clients = {}
        servers = []

        for server in org.iter_servers():
            servers.append(server)
            server_count += 1
            if server.otp_auth:
                otp_auth = True
            server_clients = server.clients
            for client_id in server_clients:
                client = server_clients[client_id]
                if client_id not in clients:
                    clients[client_id] = {}
                clients[client_id][server.id] = client

        users = []
        for user in org.iter_users(page=page, prefix=search,
                prefix_limit=limit):
            if user is None:
                search_more = False
                break
            is_client = user.id in clients
            user_dict = user.dict()
            user_dict['status'] = is_client
            user_dict['otp_auth'] = otp_auth
            server_data = []
            for server in servers:
                local_ip_addr, remote_ip_addr = server.get_ip_set(
                    org_id, user.id)
                data = {
                    'id': server.id,
                    'name': server.name,
                    'status': is_client and server.id in clients[user.id],
                    'local_address': local_ip_addr,
                    'remote_address': remote_ip_addr,
                    'real_address': None,
                    'virt_address': None,
                    'bytes_received': None,
                    'bytes_sent': None,
                    'connected_since': None,
                }
                if is_client:
                    client_data = clients[user.id].get(server.id)
                    if client_data:
                        data.update(client_data)
                server_data.append(data)
            user_dict['servers'] = server_data
            users.append(user_dict)

        if page is not None:
            return utils.jsonify({
                'page': page,
                'page_total': org.page_total,
                'server_count': server_count,
                'users': users,
            })
        elif search is not None:
            return utils.jsonify({
                'search': search,
                'search_more': search_more,
                'search_limit': limit,
                'search_count': org.get_last_prefix_count(),
                'search_time':  round((time.time() - flask.g.start), 4),
                'server_count': server_count,
                'users': users,
            })
        else:
            return utils.jsonify(users)

@app_server.app.route('/user/<org_id>', methods=['POST'])
@app_server.auth
def user_post(org_id):
    org = Organization.get_org(id=org_id)
    name = utils.filter_str(flask.request.json['name'])
    user = org.new_user(CERT_CLIENT, name)
    return utils.jsonify(user.dict())

@app_server.app.route('/user/<org_id>/<user_id>', methods=['PUT'])
@app_server.auth
def user_put(org_id, user_id):
    org = Organization.get_org(id=org_id)
    user = org.get_user(user_id)
    name = utils.filter_str(flask.request.json['name'])
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
