from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.settings import settings
from pritunl.organization import Organization
from pritunl import utils
from pritunl import logger
from pritunl import event
from pritunl import server
from pritunl.app_server import app_server
import flask
import math
import time
import collections

@app_server.app.route('/user/<org_id>', methods=['GET'])
@app_server.app.route('/user/<org_id>/<user_id>', methods=['GET'])
@app_server.app.route('/user/<org_id>/<int:page>', methods=['GET'])
@app_server.auth
def user_get(org_id, user_id=None, page=None):
    org = Organization.get_org(id=org_id)
    if user_id:
        return utils.jsonify(org.get_user(user_id).dict())

    page = flask.request.args.get('page', None)
    page = int(page) if page else page
    search = flask.request.args.get('search', None)
    limit = int(flask.request.args.get('limit', settings.user.page_count))
    otp_auth = False
    search_more = True
    server_count = 0
    clients = {}
    servers = []

    fields = (
        'name',
        'clients',
    )
    for svr in org.iter_servers(fields=fields):
        servers.append(svr)
        server_count += 1
        if svr.otp_auth:
            otp_auth = True
        server_clients = svr.clients
        for client, client_id in server_clients.iteritems():
            if client_id not in clients:
                clients[client_id] = {}
            clients[client_id][svr.id] = client

    users = []
    users_id = []
    users_server_data = collections.defaultdict(dict)
    fields = (
        'organization',
        'organization_name',
        'name',
        'email',
        'type',
        'otp_secret',
        'disabled',
    )
    for user in org.iter_users(page=page, search=search,
            search_limit=limit, fields=fields):
        user_id = user.id
        users_id.append(user_id)
        is_client = user_id in clients
        user_dict = user.dict()
        user_dict['status'] = is_client
        user_dict['otp_auth'] = otp_auth
        server_data = []
        for svr in servers:
            server_id = svr.id
            user_status = is_client and server_id in clients[user_id]
            data = {
                'id': server_id,
                'name': svr.name,
                'status': user_status,
                'local_address': None,
                'remote_address': None,
                'real_address': None,
                'virt_address': None,
                'bytes_received': None,
                'bytes_sent': None,
                'connected_since': None,
            }
            users_server_data[user_id][server_id] = data
            if user_status:
                data.update(clients[user_id][server_id])
            server_data.append(data)
        user_dict['servers'] = server_data
        users.append(user_dict)

    ip_addrs_iter = server.multi_get_ip_addr(org_id, users_id)
    for user_id, server_id, local_addr, remote_addr in ip_addrs_iter:
        user_server_data = users_server_data[user_id].get(server_id)
        if user_server_data:
            if not user_server_data['local_address']:
                user_server_data['local_address'] = local_addr
            if not user_server_data['remote_address']:
                user_server_data['remote_address'] = remote_addr

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
            'search_more': limit < org.last_search_count,
            'search_limit': limit,
            'search_count': org.last_search_count,
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
    users = []

    if isinstance(flask.request.json, list):
        users_data = flask.request.json
    else:
        users_data = [flask.request.json]

    for user_data in users_data:
        name = utils.filter_str(user_data['name'])
        email = utils.filter_str(user_data.get('email'))
        disabled = user_data.get('disabled')
        user = org.new_user(type=CERT_CLIENT, name=name, email=email,
            disabled=disabled)
        users.append(user.dict())

    event.Event(type=ORGS_UPDATED)
    event.Event(type=USERS_UPDATED, resource_id=org.id)
    event.Event(type=SERVERS_UPDATED)

    if isinstance(flask.request.json, list):
        logger.LogEntry(message='Created %s new users.' % len(
            flask.request.json))
        return utils.jsonify(users)
    else:
        logger.LogEntry(message='Created new user "%s".' % users[0]['name'])
        return utils.jsonify(users[0])

@app_server.app.route('/user/<org_id>/<user_id>', methods=['PUT'])
@app_server.auth
def user_put(org_id, user_id):
    org = Organization.get_org(id=org_id)
    user = org.get_user(user_id)

    if 'name' in flask.request.json:
        user.name = utils.filter_str(flask.request.json['name']) or None

    if 'email' in flask.request.json:
        user.email = utils.filter_str(flask.request.json['email']) or None

    disabled = flask.request.json.get('disabled')
    if disabled is not None:
        user.disabled = disabled

    user.commit()
    event.Event(type=USERS_UPDATED, resource_id=user.org.id)

    if disabled:
        if user.type == CERT_CLIENT:
            logger.LogEntry(message='Disabled user "%s".' % user.name)

        for svr in org.iter_servers():
            server_clients = svr.clients
            if user_id in server_clients:
                svr.restart()
    elif disabled == False and user.type == CERT_CLIENT:
        logger.LogEntry(message='Enabled user "%s".' % user.name)

    send_key_email = flask.request.json.get('send_key_email')
    if send_key_email and user.email:
        try:
            user.send_key_email(send_key_email)
        except EmailNotConfiguredError:
            return utils.jsonify({
                'error': EMAIL_NOT_CONFIGURED,
                'error_msg': EMAIL_NOT_CONFIGURED_MSG,
            }, 400)
        except EmailFromInvalid:
            return utils.jsonify({
                'error': EMAIL_FROM_INVALID,
                'error_msg': EMAIL_FROM_INVALID_MSG,
            }, 400)
        except EmailApiKeyInvalid:
            return utils.jsonify({
                'error': EMAIL_API_KEY_INVALID,
                'error_msg': EMAIL_API_KEY_INVALID_MSG,
            }, 400)

    return utils.jsonify(user.dict())

@app_server.app.route('/user/<org_id>/<user_id>', methods=['DELETE'])
@app_server.auth
def user_delete(org_id, user_id):
    org = Organization.get_org(id=org_id)
    user = org.get_user(user_id)
    name = user.name
    user.remove()

    event.Event(type=ORGS_UPDATED)
    event.Event(type=USERS_UPDATED, resource_id=org.id)

    for svr in org.iter_servers():
        server_clients = svr.clients
        if user_id in server_clients:
            svr.restart()

    logger.LogEntry(message='Deleted user "%s".' % name)

    return utils.jsonify({})

@app_server.app.route('/user/<org_id>/<user_id>/otp_secret', methods=['PUT'])
@app_server.auth
def user_otp_secret_put(org_id, user_id):
    org = Organization.get_org(id=org_id)
    user = org.get_user(user_id)
    user.generate_otp_secret()
    user.commit()
    event.Event(type=USERS_UPDATED, resource_id=org.id)
    return utils.jsonify(user.dict())
