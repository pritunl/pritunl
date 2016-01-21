from pritunl.constants import *
from pritunl.exceptions import *
from pritunl import settings
from pritunl import utils
from pritunl import logger
from pritunl import event
from pritunl import server
from pritunl import organization
from pritunl import app
from pritunl import auth
from pritunl import mongo
from pritunl import messenger
from pritunl import ipaddress

import flask
import time
import base64
import hmac
import hashlib
import pymongo

def _network_link_invalid():
    return utils.jsonify({
        'error': NETWORK_LINK_INVALID,
        'error_msg': NETWORK_LINK_INVALID_MSG,
    }, 400)

@app.app.route('/user/<org_id>', methods=['GET'])
@app.app.route('/user/<org_id>/<user_id>', methods=['GET'])
@app.app.route('/user/<org_id>/<int:page>', methods=['GET'])
@auth.session_auth
def user_get(org_id, user_id=None, page=None):
    org = organization.get_by_id(org_id)
    if user_id:
        return utils.jsonify(org.get_user(user_id).dict())

    page = flask.request.args.get('page', None)
    page = int(page) if page else page
    search = flask.request.args.get('search', None)
    limit = int(flask.request.args.get('limit', settings.user.page_count))
    otp_auth = False
    dns_mapping = False
    server_count = 0
    servers = []

    for svr in org.iter_servers(fields=('name', 'otp_auth', 'dns_mapping')):
        servers.append(svr)
        server_count += 1
        if svr.otp_auth:
            otp_auth = True
        if svr.dns_mapping:
            dns_mapping = True

    users = []
    users_id = []
    users_data = {}
    users_servers = {}
    fields = (
        'organization',
        'organization_name',
        'name',
        'email',
        'pin',
        'type',
        'auth_type',
        'otp_secret',
        'disabled',
        'bypass_secondary',
        'dns_servers',
        'dns_suffix',
        'port_forwarding',
    )
    for usr in org.iter_users(page=page, search=search,
            search_limit=limit, fields=fields):
        users_id.append(usr.id)

        user_dict = usr.dict()
        user_dict['gravatar'] = settings.user.gravatar
        user_dict['audit'] = settings.app.auditing == ALL
        user_dict['status'] = False
        user_dict['sso'] = settings.app.sso
        user_dict['otp_auth'] = otp_auth
        if dns_mapping:
            user_dict['dns_mapping'] = ('%s.%s.vpn' % (
                usr.name.split('@')[0], org.name)).lower()
        else:
            user_dict['dns_mapping'] = None
        user_dict['network_links'] = []

        users_data[usr.id] = user_dict
        users_servers[usr.id] = {}

        server_data = []
        for svr in servers:
            data = {
                'id': svr.id,
                'name': svr.name,
                'status': False,
                'server_id': svr.id,
                'device_name': None,
                'platform': None,
                'real_address': None,
                'virt_address': None,
                'virt_address6': None,
                'connected_since': None
            }
            server_data.append(data)
            users_servers[usr.id][svr.id] = data

        user_dict['servers'] = sorted(server_data, key=lambda x: x['name'])

        users.append(user_dict)

    clients_collection = mongo.get_collection('clients')
    for doc in clients_collection.find({
                'user_id': {'$in': users_id},
            }):
        server_data = users_servers[doc['user_id']].get(doc['server_id'])
        if not server_data:
            continue

        users_data[doc['user_id']]['status'] = True

        if server_data['status']:
            server_data = {
                'name': server_data['name'],
            }
            append = True
        else:
            append = False

        virt_address6 = doc.get('virt_address6')
        if virt_address6:
            server_data['virt_address6'] = virt_address6.split('/')[0]

        server_data['id'] = doc['_id']
        server_data['status'] = True
        server_data['server_id'] = server_data['id']
        server_data['device_name'] = doc['device_name']
        server_data['platform'] = doc['platform']
        server_data['real_address'] = doc['real_address']
        server_data['virt_address'] = doc['virt_address'].split('/')[0]
        server_data['connected_since'] = doc['connected_since']

        if append:
            svrs = users_data[doc['user_id']]['servers']
            svrs.append(server_data)
            users_data[doc['user_id']]['servers'] = sorted(
                svrs, key=lambda x: x['name'])

    net_link_collection = mongo.get_collection('users_net_link')
    for doc in net_link_collection.find({
                'user_id': {'$in': users_id},
            }):
        users_data[doc['user_id']]['network_links'].append(doc['network'])

    ip_addrs_iter = server.multi_get_ip_addr(org_id, users_id)
    for user_id, server_id, addr, addr6 in ip_addrs_iter:
        server_data = users_servers[user_id].get(server_id)
        if server_data:
            if not server_data['virt_address']:
                server_data['virt_address'] = addr
            if not server_data['virt_address6']:
                server_data['virt_address6'] = addr6

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

@app.app.route('/user/<org_id>', methods=['POST'])
@auth.session_auth
def user_post(org_id):
    if settings.app.demo_mode:
        return utils.demo_blocked()

    org = organization.get_by_id(org_id)
    users = []

    if isinstance(flask.request.json, list):
        users_data = flask.request.json
    else:
        users_data = [flask.request.json]

    try:
        for user_data in users_data:
            name = utils.filter_str(user_data['name'])
            email = utils.filter_str(user_data.get('email'))
            pin = utils.filter_str(user_data.get('pin')) or None
            disabled = user_data.get('disabled')
            network_links = user_data.get('network_links')
            bypass_secondary = user_data.get('bypass_secondary')
            dns_servers = user_data.get('dns_servers') or None
            dns_suffix = utils.filter_str(user_data.get('dns_suffix')) or None
            port_forwarding_in = user_data.get('port_forwarding')
            port_forwarding = []

            if pin:
                if not pin.isdigit():
                    return utils.jsonify({
                        'error': PIN_NOT_DIGITS,
                        'error_msg': PIN_NOT_DIGITS_MSG,
                    }, 400)

                if len(pin) < settings.user.pin_min_length:
                    return utils.jsonify({
                        'error': PIN_TOO_SHORT,
                        'error_msg': PIN_TOO_SHORT_MSG,
                    }, 400)

                pin = auth.generate_hash_pin_v1(pin)

            if port_forwarding_in:
                for data in port_forwarding_in:
                    port_forwarding.append({
                        'protocol': utils.filter_str(data.get('protocol')),
                        'port': utils.filter_str(data.get('port')),
                        'dport': utils.filter_str(data.get('dport')),
                    })

            user = org.new_user(type=CERT_CLIENT, name=name, email=email,
                pin=pin, disabled=disabled, bypass_secondary=bypass_secondary,
                dns_servers=dns_servers, dns_suffix=dns_suffix,
                port_forwarding=port_forwarding)
            user.audit_event('user_created',
                'User created from web console',
                remote_addr=utils.get_remote_addr(),
            )

            if network_links:
                for network_link in network_links:
                    try:
                        user.add_network_link(network_link)
                    except (ipaddress.AddressValueError, ValueError):
                        return _network_link_invalid()
                    except ServerOnlineError:
                        return utils.jsonify({
                            'error': NETWORK_LINK_NOT_OFFLINE,
                            'error_msg': NETWORK_LINK_NOT_OFFLINE_MSG,
                        }, 400)

            users.append(user.dict())
    finally:
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

@app.app.route('/user/<org_id>/<user_id>', methods=['PUT'])
@auth.session_auth
def user_put(org_id, user_id):
    if settings.app.demo_mode:
        return utils.demo_blocked()

    org = organization.get_by_id(org_id)
    user = org.get_user(user_id)
    reset_user = False
    port_forwarding_event = False

    if 'name' in flask.request.json:
        name = utils.filter_str(flask.request.json['name']) or None

        if name != user.name:
            user.audit_event('user_updated',
                'User name changed',
                remote_addr=utils.get_remote_addr(),
            )

        user.name = name

    if 'email' in flask.request.json:
        email = utils.filter_str(flask.request.json['email']) or None

        if email != user.email:
            user.audit_event('user_updated',
                'User email changed',
                remote_addr=utils.get_remote_addr(),
            )

        user.email = email

    if 'pin' in flask.request.json:
        pin = flask.request.json['pin']

        if pin != True:
            if pin:
                if not pin.isdigit():
                    return utils.jsonify({
                        'error': PIN_NOT_DIGITS,
                        'error_msg': PIN_NOT_DIGITS_MSG,
                    }, 400)

                if len(pin) < settings.user.pin_min_length:
                    return utils.jsonify({
                        'error': PIN_TOO_SHORT,
                        'error_msg': PIN_TOO_SHORT_MSG,
                    }, 400)

            if pin != user.pin:
                user.audit_event('user_updated',
                    'User pin changed',
                    remote_addr=utils.get_remote_addr(),
                )

            user.set_pin(pin)

    if 'network_links' in flask.request.json:
        network_links_cur = set(user.get_network_links())
        network_links_new = set()

        for network_link in flask.request.json['network_links']:
            try:
                network_link = str(ipaddress.IPNetwork(network_link))
            except (ipaddress.AddressValueError, ValueError):
                return _network_link_invalid()
            network_links_new.add(network_link)

        network_links_add = network_links_new - network_links_cur
        network_links_rem = network_links_cur - network_links_new

        if len(network_links_add) or len(network_links_rem):
            reset_user = True
            user.audit_event('user_updated',
                'User network links updated',
                remote_addr=utils.get_remote_addr(),
            )

        try:
            for network_link in network_links_add:
                user.add_network_link(network_link)
        except ServerOnlineError:
            return utils.jsonify({
                'error': NETWORK_LINK_NOT_OFFLINE,
                'error_msg': NETWORK_LINK_NOT_OFFLINE_MSG,
            }, 400)

        for network_link in network_links_rem:
            user.remove_network_link(network_link)

    if 'port_forwarding' in flask.request.json:
        port_forwarding = []
        for data in flask.request.json['port_forwarding']:
            port_forwarding.append({
                'protocol': utils.filter_str(data.get('protocol')),
                'port': utils.filter_str(data.get('port')),
                'dport': utils.filter_str(data.get('dport')),
            })

        port_forwarding_event = port_forwarding != user.port_forwarding

        if port_forwarding_event:
            user.audit_event('user_updated',
                'User port forwarding changed',
                remote_addr=utils.get_remote_addr(),
            )

        user.port_forwarding = port_forwarding

    disabled = flask.request.json.get('disabled')
    if disabled is not None:
        if disabled != user.disabled:
            user.audit_event('user_updated',
                'User %s' % ('disabled' if disabled else 'enabled'),
                remote_addr=utils.get_remote_addr(),
            )

        user.disabled = disabled

    bypass_secondary = flask.request.json.get('bypass_secondary')
    if bypass_secondary is not None:
        user.bypass_secondary = bypass_secondary

    if 'dns_servers' in flask.request.json:
        dns_servers = flask.request.json['dns_servers'] or None
        if user.dns_servers != dns_servers:
            user.audit_event('user_updated',
                'User dns servers changed',
                remote_addr=utils.get_remote_addr(),
            )
            reset_user = True
        user.dns_servers = dns_servers

    if 'dns_suffix' in flask.request.json:
        dns_suffix = utils.filter_str(
            flask.request.json['dns_suffix']) or None
        if user.dns_suffix != dns_suffix:
            user.audit_event('user_updated',
                'User dns suffix changed',
                remote_addr=utils.get_remote_addr(),
            )
            reset_user = True
        user.dns_suffix = dns_suffix

    user.commit()
    event.Event(type=USERS_UPDATED, resource_id=user.org.id)
    if port_forwarding_event:
        messenger.publish('port_forwarding', {
            'org_id': org.id,
            'user_id': user.id,
        })

    if reset_user or disabled:
        user.disconnect()

    if disabled:
        if user.type == CERT_CLIENT:
            logger.LogEntry(message='Disabled user "%s".' % user.name)
    elif disabled == False and user.type == CERT_CLIENT:
        logger.LogEntry(message='Enabled user "%s".' % user.name)

    send_key_email = flask.request.json.get('send_key_email')
    if send_key_email and user.email:
        user.audit_event('user_emailed',
            'User key email sent to "%s"' % user.email,
            remote_addr=utils.get_remote_addr(),
        )

        try:
            user.send_key_email(flask.request.url_root[:-1])
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
        except EmailAuthInvalid:
            return utils.jsonify({
                'error': EMAIL_AUTH_INVALID,
                'error_msg': EMAIL_AUTH_INVALID_MSG,
            }, 400)

    return utils.jsonify(user.dict())

@app.app.route('/user/<org_id>/<user_id>', methods=['DELETE'])
@auth.session_auth
def user_delete(org_id, user_id):
    if settings.app.demo_mode:
        return utils.demo_blocked()

    org = organization.get_by_id(org_id)
    user = org.get_user(user_id)
    name = user.name
    user.remove()

    event.Event(type=ORGS_UPDATED)
    event.Event(type=USERS_UPDATED, resource_id=org.id)

    user.disconnect()

    logger.LogEntry(message='Deleted user "%s".' % name)

    return utils.jsonify({})

@app.app.route('/user/<org_id>/<user_id>/otp_secret', methods=['PUT'])
@auth.session_auth
def user_otp_secret_put(org_id, user_id):
    if settings.app.demo_mode:
        return utils.demo_blocked()

    org = organization.get_by_id(org_id)
    user = org.get_user(user_id)

    user.audit_event('user_updated',
        'User two step secret reset',
        remote_addr=utils.get_remote_addr(),
    )

    user.generate_otp_secret()
    user.commit()
    event.Event(type=USERS_UPDATED, resource_id=org.id)
    return utils.jsonify(user.dict())

@app.app.route('/user/<org_id>/<user_id>/audit', methods=['GET'])
@auth.session_auth
def user_audit_get(org_id, user_id):
    org = organization.get_by_id(org_id)
    user = org.get_user(user_id)

    return utils.jsonify(user.get_audit_events())

@app.app.route('/auth/user', methods=['POST'])
def auth_user_post():
    auth_token = flask.request.headers.get('Auth-Token', None)
    auth_timestamp = flask.request.headers.get('Auth-Timestamp', None)
    auth_nonce = flask.request.headers.get('Auth-Nonce', None)
    auth_signature = flask.request.headers.get('Auth-Signature', None)

    if not auth_token or not auth_timestamp or not auth_nonce or \
            not auth_signature:
        return utils.jsonify({
            'error': AUTH_INVALID,
            'error_msg': AUTH_INVALID_MSG,
        }, 401)
    auth_nonce = auth_nonce[:32]

    try:
        if abs(int(auth_timestamp) - int(utils.time_now())) > \
                settings.app.auth_time_window:
            return utils.jsonify({
                'error': AUTH_INVALID,
                'error_msg': AUTH_INVALID_MSG,
            }, 401)
    except ValueError:
        return utils.jsonify({
            'error': AUTH_INVALID,
            'error_msg': AUTH_INVALID_MSG,
        }, 401)

    org = organization.get_by_token(auth_token)
    if not org:
        return utils.jsonify({
            'error': AUTH_INVALID,
            'error_msg': AUTH_INVALID_MSG,
        }, 401)

    auth_string = '&'.join([
        auth_token,
        auth_timestamp,
        auth_nonce,
        flask.request.method,
        flask.request.path,
    ] + ([flask.request.data] if flask.request.data else []))

    if len(auth_string) > AUTH_SIG_STRING_MAX_LEN:
        return utils.jsonify({
            'error': AUTH_INVALID,
            'error_msg': AUTH_INVALID_MSG,
        }, 401)

    if not org.auth_secret or len(org.auth_secret) < 8:
        return utils.jsonify({
            'error': AUTH_INVALID,
            'error_msg': AUTH_INVALID_MSG,
        }, 401)

    auth_test_signature = base64.b64encode(hmac.new(
        org.auth_secret.encode(), auth_string,
        hashlib.sha256).digest())
    if auth_signature != auth_test_signature:
        return utils.jsonify({
            'error': AUTH_INVALID,
            'error_msg': AUTH_INVALID_MSG,
        }, 401)

    try:
        org.nonces_collection.insert({
            'token': auth_token,
            'nonce': auth_nonce,
            'timestamp': utils.now(),
        })
    except pymongo.errors.DuplicateKeyError:
        return utils.jsonify({
            'error': AUTH_INVALID,
            'error_msg': AUTH_INVALID_MSG,
        }, 401)

    username = flask.request.json['username']
    network_links = flask.request.json.get('network_links')

    usr = org.find_user(name=username)
    if not usr:
        usr = org.new_user(name=username, type=CERT_CLIENT)
        usr.audit_event('user_created',
            'User created with authentication token',
            remote_addr=utils.get_remote_addr())

        if network_links:
            for network_link in network_links:
                try:
                    usr.add_network_link(network_link, force=True)
                except (ipaddress.AddressValueError, ValueError):
                    return _network_link_invalid()

        event.Event(type=ORGS_UPDATED)
        event.Event(type=USERS_UPDATED, resource_id=org.id)
        event.Event(type=SERVERS_UPDATED)

    keys = {}
    for svr in org.iter_servers():
        key = usr.build_key_conf(svr.id)
        keys[key['name']] = key['conf']

    return utils.jsonify(keys)
