from pritunl.constants import *
from pritunl.exceptions import *
from pritunl import settings
from pritunl import utils
from pritunl import logger
from pritunl import event
from pritunl import server
from pritunl import host
from pritunl import organization
from pritunl import app
from pritunl import auth
from pritunl import mongo
from pritunl import messenger
from pritunl import ipaddress
from pritunl import callqueue
from pritunl import journal

import flask
import time
import threading

_users_background = False
_users_background_lock = threading.Lock()

def _network_link_invalid():
    return utils.jsonify({
        'error': NETWORK_LINK_INVALID,
        'error_msg': NETWORK_LINK_INVALID_MSG,
    }, 400)

@app.app.route('/user/<org_id>', methods=['GET'])
@app.app.route('/user/<org_id>/<user_id>', methods=['GET'])
@auth.session_auth
def user_get(org_id, user_id=None, page=None):
    if settings.app.demo_mode and user_id:
        resp = utils.demo_get_cache()
        if resp:
            return utils.jsonify(resp)

    org = organization.get_by_id(org_id)
    if not org:
        return flask.abort(404)

    page = flask.request.args.get('page', page)
    page = int(page) if page else page
    search = flask.request.args.get('search', None)
    limit = int(flask.request.args.get('limit', settings.user.page_count))
    otp_auth = False
    dns_mapping = False
    server_count = 0
    servers = []

    if settings.app.demo_mode:
        resp = utils.demo_get_cache(page, search, limit)
        if resp:
            return utils.jsonify(resp)

    for svr in org.iter_servers(fields=('name', 'otp_auth',
            'dns_mapping', 'groups')):
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
        'groups',
        'pin',
        'type',
        'auth_type',
        'otp_secret',
        'yubico_id',
        'disabled',
        'bypass_secondary',
        'client_to_client',
        'mac_addresses',
        'dns_servers',
        'dns_suffix',
        'port_forwarding',
    )

    if user_id:
        usr = org.get_user(user_id)
        if not usr:
            return flask.abort(404)

        query = [usr]
    else:
        query = org.iter_users(page=page, search=search,
            search_limit=limit, fields=fields)

    for usr in query:
        users_id.append(usr.id)

        user_dict = usr.dict()
        user_dict['gravatar'] = settings.user.gravatar
        user_dict['audit'] = settings.app.auditing == ALL
        user_dict['status'] = False
        user_dict['sso'] = settings.app.sso

        if otp_auth and not usr.has_duo_passcode and not usr.has_yubikey:
            user_dict['otp_auth'] = True
        else:
            user_dict['otp_auth'] = False

        if dns_mapping:
            user_dict['dns_mapping'] = ('%s.%s.vpn' % (
                str(usr.name).split('@')[0], org.name)).lower()
        else:
            user_dict['dns_mapping'] = None
        user_dict['network_links'] = []

        users_data[usr.id] = user_dict
        users_servers[usr.id] = {}

        server_data = []
        for svr in servers:
            if not svr.check_groups(usr.groups):
                continue
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
                'connected_since': None,
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
    for usr_id, server_id, addr, addr6 in ip_addrs_iter:
        server_data = users_servers[usr_id].get(server_id)
        if server_data:
            if not server_data['virt_address']:
                server_data['virt_address'] = addr
            if not server_data['virt_address6']:
                server_data['virt_address6'] = addr6

    if user_id:
        resp = users[0]
        if settings.app.demo_mode:
            utils.demo_set_cache(resp)
        return utils.jsonify(resp)
    elif page is not None:
        resp = {
            'page': page,
            'page_total': org.page_total,
            'server_count': server_count,
            'users': users,
        }
    elif search is not None:
        resp = {
            'search': search,
            'search_more': limit < org.last_search_count,
            'search_limit': limit,
            'search_count': org.last_search_count,
            'search_time':  round((time.time() - flask.g.start), 4),
            'server_count': server_count,
            'users': users,
        }
    else:
        resp = users

    if settings.app.demo_mode and not search:
        utils.demo_set_cache(resp, page, search, limit)
    return utils.jsonify(resp)

def _create_user(users, org, user_data, remote_addr, pool):
    name = utils.filter_str(user_data['name'])
    email = utils.filter_str(user_data.get('email'))
    auth_type = utils.filter_str(user_data.get('auth_type'))
    pin = utils.filter_str(user_data.get('pin')) or None
    disabled = True if user_data.get('disabled') else False
    network_links = user_data.get('network_links') or None
    bypass_secondary = True if user_data.get(
        'bypass_secondary') else False
    client_to_client = True if user_data.get(
        'client_to_client') else False
    mac_addresses = user_data.get('mac_addresses') or None
    dns_servers = user_data.get('dns_servers') or None
    dns_suffix = utils.filter_str(user_data.get('dns_suffix')) or None
    port_forwarding_in = user_data.get('port_forwarding')
    port_forwarding = []

    if auth_type not in AUTH_TYPES:
        auth_type = LOCAL_AUTH

    if auth_type == YUBICO_AUTH:
        yubico_id = user_data.get('yubico_id')
        yubico_id = yubico_id[:12] if yubico_id else None
    else:
        yubico_id = None

    groups = user_data.get('groups') or []
    for i, group in enumerate(groups):
        groups[i] = utils.filter_str(group)
    groups = list(set(groups))

    if pin:
        if settings.user.pin_digits_only and not pin.isdigit():
            return utils.jsonify({
                'error': PIN_NOT_DIGITS,
                'error_msg': PIN_NOT_DIGITS_MSG,
            }, 400)

        if len(pin) < settings.user.pin_min_length:
            return utils.jsonify({
                'error': PIN_TOO_SHORT,
                'error_msg': PIN_TOO_SHORT_MSG,
            }, 400)

        pin = auth.generate_hash_pin_v2(pin)

    if bypass_secondary:
        if pin:
            return utils.jsonify({
                'error': PIN_BYPASS_SECONDARY,
                'error_msg': PIN_BYPASS_SECONDARY_MSG,
            }, 400)
        if yubico_id:
            return utils.jsonify({
                'error': YUBIKEY_BYPASS_SECONDARY,
                'error_msg': YUBIKEY_BYPASS_SECONDARY_MSG,
            }, 400)

    if port_forwarding_in:
        for data in port_forwarding_in:
            port_forwarding.append({
                'protocol': utils.filter_str(data.get('protocol')),
                'port': utils.filter_str(data.get('port')),
                'dport': utils.filter_str(data.get('dport')),
            })

    user = org.new_user(type=CERT_CLIENT, pool=pool, name=name,
        email=email, auth_type=auth_type, yubico_id=yubico_id, groups=groups,
        pin=pin, disabled=disabled, bypass_secondary=bypass_secondary,
        client_to_client=client_to_client, mac_addresses=mac_addresses,
        dns_servers=dns_servers,dns_suffix=dns_suffix,
        port_forwarding=port_forwarding)
    user.audit_event('user_created',
        'User created from web console',
        remote_addr=remote_addr,
    )

    journal.entry(
        journal.USER_CREATE,
        user.journal_data,
        event_long='User created from web console',
        remote_address=remote_addr,
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

def _create_users(org_id, users_data, remote_addr, background):
    global _users_background

    org = organization.get_by_id(org_id)
    users = []
    hosts_online = host.get_hosts_online()

    if background:
        user_queue = callqueue.CallQueue(maxsize=hosts_online)
        user_queue.start(hosts_online)
        _users_background_lock.acquire()
        if _users_background:
            return
        _users_background = True
        _users_background_lock.release()

    try:
        if background:
            for i, user_data in enumerate(users_data):
                user_queue.put(_create_user, users, org,
                    user_data, remote_addr, False)
        else:
            for i, user_data in enumerate(users_data):
                err = _create_user(users, org, user_data, remote_addr, True)
                if err:
                    return err
    except:
        logger.exception('Error creating users', 'users')
        raise
    finally:
        if background:
            user_queue.close()
            _users_background_lock.acquire()
            _users_background = False
            _users_background_lock.release()

        event.Event(type=ORGS_UPDATED)
        event.Event(type=USERS_UPDATED, resource_id=org.id)
        event.Event(type=SERVERS_UPDATED)

    if len(users) == 1:
        logger.LogEntry(message='Created new user.')
    else:
        logger.LogEntry(message='Created %s new users.' % len(users))
    return utils.jsonify(users)

@app.app.route('/user/<org_id>', methods=['POST'])
@app.app.route('/user/<org_id>/multi', methods=['POST'])
@auth.session_auth
def user_post(org_id):
    if settings.app.demo_mode:
        return utils.demo_blocked()

    remote_addr = utils.get_remote_addr()

    if isinstance(flask.request.json, list):
        users_data = flask.request.json
    else:
        users_data = [flask.request.json]

    if len(users_data) > 10:
        if _users_background:
            return utils.jsonify({
                'error': USERS_BACKGROUND_BUSY,
                'error_msg': USERS_BACKGROUND_BUSY_MSG,
            }, 429)

        thread = threading.Thread(
            target=_create_users,
            args=(org_id, users_data, remote_addr, True),
        )
        thread.daemon = True
        thread.start()

        return utils.jsonify({
            'status': USERS_BACKGROUND,
            'status_msg': USERS_BACKGROUND_MSG,
        }, 202)

    return _create_users(org_id, users_data, remote_addr, False)

@app.app.route('/user/<org_id>/<user_id>', methods=['PUT'])
@auth.session_auth
def user_put(org_id, user_id):
    if settings.app.demo_mode:
        return utils.demo_blocked()

    org = organization.get_by_id(org_id)
    user = org.get_user(user_id)
    reset_user = False
    reset_user_cache = False
    port_forwarding_event = False
    remote_addr = utils.get_remote_addr()

    if 'name' in flask.request.json:
        name = utils.filter_str(flask.request.json['name']) or 'undefined'

        if name != user.name:
            user.audit_event('user_updated',
                'User name changed',
                remote_addr=remote_addr,
            )

            journal.entry(
                journal.USER_UPDATE,
                user.journal_data,
                event_long='User name changed',
                remote_address=remote_addr,
            )

        user.name = name

    if 'email' in flask.request.json:
        email = utils.filter_str(flask.request.json['email']) or None

        if email != user.email:
            user.audit_event('user_updated',
                'User email changed',
                remote_addr=remote_addr,
            )

            journal.entry(
                journal.USER_UPDATE,
                user.journal_data,
                event_long='User email changed',
                remote_address=remote_addr,
            )

        user.email = email

    if 'auth_type' in flask.request.json:
        auth_type = utils.filter_str(flask.request.json['auth_type']) or None

        if auth_type in AUTH_TYPES:
            if auth_type != user.auth_type:
                reset_user = True
                reset_user_cache = True
            user.auth_type = auth_type

    if 'yubico_id' in flask.request.json and user.auth_type == YUBICO_AUTH:
        yubico_id = utils.filter_str(flask.request.json['yubico_id']) or None
        yubico_id = yubico_id[:12] if yubico_id else None
        if yubico_id != user.yubico_id:
            reset_user = True
            reset_user_cache = True
        user.yubico_id = yubico_id

    if 'groups' in flask.request.json:
        groups = flask.request.json['groups'] or []
        for i, group in enumerate(groups):
            groups[i] = utils.filter_str(group)
        groups = set(groups)

        if groups != set(user.groups or []):
            user.audit_event('user_updated',
                'User groups changed',
                remote_addr=remote_addr,
            )

            journal.entry(
                journal.USER_UPDATE,
                user.journal_data,
                event_long='User groups changed',
                remote_address=remote_addr,
            )

        user.groups = list(groups)

    if 'pin' in flask.request.json:
        pin = flask.request.json['pin'] or None

        if pin is not True:
            if pin:
                if settings.user.pin_mode == PIN_DISABLED:
                    return utils.jsonify({
                        'error': PIN_IS_DISABLED,
                        'error_msg': PIN_IS_DISABLED_MSG,
                    }, 400)

                if RADIUS_AUTH in user.auth_type:
                    return utils.jsonify({
                        'error': PIN_RADIUS,
                        'error_msg': PIN_RADIUS_MSG,
                    }, 400)

                if settings.user.pin_digits_only and not pin.isdigit():
                    return utils.jsonify({
                        'error': PIN_NOT_DIGITS,
                        'error_msg': PIN_NOT_DIGITS_MSG,
                    }, 400)

                if len(pin) < settings.user.pin_min_length:
                    return utils.jsonify({
                        'error': PIN_TOO_SHORT,
                        'error_msg': PIN_TOO_SHORT_MSG,
                    }, 400)

            if user.set_pin(pin):
                reset_user = True
                reset_user_cache = True

                user.audit_event('user_updated',
                    'User pin changed',
                    remote_addr=remote_addr,
                )

                journal.entry(
                    journal.USER_UPDATE,
                    user.journal_data,
                    event_long='User pin changed',
                    remote_address=remote_addr,
                )

    if 'network_links' in flask.request.json:
        network_links_cur = set(user.get_network_links())
        network_links_new = set()

        for network_link in flask.request.json['network_links'] or []:
            try:
                network_link = str(ipaddress.ip_network(network_link))
            except (ipaddress.AddressValueError, ValueError):
                return _network_link_invalid()
            network_links_new.add(network_link)

        network_links_add = network_links_new - network_links_cur
        network_links_rem = network_links_cur - network_links_new

        if len(network_links_add) or len(network_links_rem):
            reset_user = True
            user.audit_event('user_updated',
                'User network links updated',
                remote_addr=remote_addr,
            )

            journal.entry(
                journal.USER_UPDATE,
                user.journal_data,
                event_long='User network links updated',
                remote_address=remote_addr,
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
        for data in flask.request.json['port_forwarding'] or []:
            port_forwarding.append({
                'protocol': utils.filter_str(data.get('protocol')),
                'port': utils.filter_str(data.get('port')),
                'dport': utils.filter_str(data.get('dport')),
            })

        if port_forwarding != user.port_forwarding:
            port_forwarding_event = True
            user.audit_event('user_updated',
                'User port forwarding changed',
                remote_addr=remote_addr,
            )

            journal.entry(
                journal.USER_UPDATE,
                user.journal_data,
                event_long='User port forwarding changed',
                remote_address=remote_addr,
            )

        user.port_forwarding = port_forwarding

    disabled = True if flask.request.json.get('disabled') else False
    if disabled != user.disabled:
        user.audit_event('user_updated',
            'User %s' % ('disabled' if disabled else 'enabled'),
            remote_addr=remote_addr,
        )

        journal.entry(
            journal.USER_UPDATE,
            user.journal_data,
            event_long='User %s' % ('disabled' if disabled else 'enabled'),
            remote_address=remote_addr,
        )

        if disabled:
            reset_user = True
            reset_user_cache = True
    user.disabled = disabled

    user.bypass_secondary = True if flask.request.json.get(
        'bypass_secondary') else False

    user.client_to_client = True if flask.request.json.get(
        'client_to_client') else False

    if user.bypass_secondary:
        if user.pin:
            return utils.jsonify({
                'error': PIN_BYPASS_SECONDARY,
                'error_msg': PIN_BYPASS_SECONDARY_MSG,
            }, 400)
        if user.yubico_id:
            return utils.jsonify({
                'error': YUBIKEY_BYPASS_SECONDARY,
                'error_msg': YUBIKEY_BYPASS_SECONDARY_MSG,
            }, 400)

    if 'mac_addresses' in flask.request.json:
        mac_addresses = flask.request.json['mac_addresses'] or None
        if user.mac_addresses != mac_addresses:
            user.audit_event('user_updated',
                'User mac addresses changed',
                remote_addr=remote_addr,
            )

            journal.entry(
                journal.USER_UPDATE,
                user.journal_data,
                event_long='User mac addresses changed',
                remote_address=remote_addr,
            )

            reset_user = True
        user.mac_addresses = mac_addresses

    if 'dns_servers' in flask.request.json:
        dns_servers = flask.request.json['dns_servers'] or None
        if user.dns_servers != dns_servers:
            user.audit_event('user_updated',
                'User dns servers changed',
                remote_addr=remote_addr,
            )

            journal.entry(
                journal.USER_UPDATE,
                user.journal_data,
                event_long='User dns servers changed',
                remote_address=remote_addr,
            )

            reset_user = True
        user.dns_servers = dns_servers

    if 'dns_suffix' in flask.request.json:
        dns_suffix = utils.filter_str(
            flask.request.json['dns_suffix']) or None
        if user.dns_suffix != dns_suffix:
            user.audit_event('user_updated',
                'User dns suffix changed',
                remote_addr=remote_addr,
            )

            journal.entry(
                journal.USER_UPDATE,
                user.journal_data,
                event_long='User dns suffix changed',
                remote_address=remote_addr,
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

    if reset_user_cache:
        user.clear_auth_cache()
    if reset_user:
        user.disconnect()

    send_key_email = flask.request.json.get('send_key_email')
    if send_key_email and user.email:
        user.audit_event('user_emailed',
            'User key email sent to "%s"' % user.email,
            remote_addr=remote_addr,
        )

        journal.entry(
            journal.USER_PROFILE_EMAIL,
            user.journal_data,
            event_long='User key email sent to "%s"' % user.email,
            remote_address=remote_addr,
        )

        try:
            user.send_key_email(utils.get_url_root())
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

    remote_addr = utils.get_remote_addr()
    org = organization.get_by_id(org_id)
    user = org.get_user(user_id)
    name = user.name

    journal.entry(
        journal.USER_DELETE,
        user.journal_data,
        event_long='User deleted',
        remote_address=remote_addr,
    )

    user.remove()

    event.Event(type=ORGS_UPDATED)
    event.Event(type=USERS_UPDATED, resource_id=org.id)

    user.clear_auth_cache()
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
    remote_addr = utils.get_remote_addr()

    user.audit_event('user_updated',
        'User two step secret reset',
        remote_addr=remote_addr,
    )

    journal.entry(
        journal.USER_UPDATE,
        user.journal_data,
        event_long='User two step secret reset',
        remote_address=remote_addr,
    )

    user.generate_otp_secret()
    user.commit()
    event.Event(type=USERS_UPDATED, resource_id=org.id)
    return utils.jsonify(user.dict())

@app.app.route('/user/<org_id>/<user_id>/audit', methods=['GET'])
@auth.session_auth
def user_audit_get(org_id, user_id):
    if settings.app.demo_mode:
        resp = utils.demo_get_cache()
        if resp:
            return utils.jsonify(resp)

    org = organization.get_by_id(org_id)
    user = org.get_user(user_id)

    resp = user.get_audit_events()
    if settings.app.demo_mode:
        utils.demo_set_cache(resp)
    return utils.jsonify(resp)
