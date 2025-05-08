from pritunl.constants import *
from pritunl.exceptions import *
from pritunl import app
from pritunl import auth
from pritunl import settings
from pritunl import utils
from pritunl import mongo
from pritunl import link
from pritunl import event
from pritunl import database

import pymongo
import flask
import base64
import hmac
import hashlib
import json
import os
import random
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import (
    Cipher, algorithms, modes
)

@app.app.route('/link', methods=['GET'])
@auth.session_auth
def link_get():
    if not settings.local.sub_plan or \
            'enterprise' not in settings.local.sub_plan:
        return flask.abort(404)

    if settings.app.demo_mode:
        resp = utils.demo_get_cache()
        if resp:
            return utils.jsonify(resp)

    page = flask.request.args.get('page', None)
    page = int(page) if page else page

    links = []
    for lnk in link.iter_links(page):
        links.append(lnk.dict())

    data = {
        'page': page,
        'page_total': link.get_page_total(),
        'links': links,
    }

    if settings.app.demo_mode:
        utils.demo_set_cache(data)
    return utils.jsonify(data)

@app.app.route('/link', methods=['POST'])
@auth.session_auth
def link_post():
    if not settings.local.sub_plan or \
            'enterprise' not in settings.local.sub_plan:
        return flask.abort(404)

    if settings.app.demo_mode:
        return utils.demo_blocked()

    name = utils.filter_str(flask.request.json.get('name')) or 'undefined'
    type = DIRECT if flask.request.json.get('type') == DIRECT \
        else SITE_TO_SITE
    ipv6 = True if flask.request.json.get('ipv6') else False

    if flask.request.json.get('protocol') == 'wg':
        protocol = 'wg'
    else:
        protocol = 'ipsec'

    wg_port = flask.request.json.get('wg_port')
    if not wg_port or wg_port < 1 or wg_port > 65535:
        wg_port = random.randint(30000, 32500)

    host_check = True if flask.request.json.get('host_check') else False
    action = RESTART if flask.request.json.get(
        'action') == RESTART else HOLD
    preferred_ike = utils.filter_str2(
        flask.request.json.get('preferred_ike')) or None
    preferred_esp = utils.filter_str2(
        flask.request.json.get('preferred_esp')) or None
    force_preferred = True if flask.request.json.get(
        'force_preferred') else False

    lnk = link.Link(
        name=name,
        type=type,
        status=ONLINE,
        ipv6=ipv6,
        protocol=protocol,
        wg_port=wg_port,
        host_check=host_check,
        action=action,
        preferred_ike=preferred_ike,
        preferred_esp=preferred_esp,
        force_preferred=force_preferred,
    )

    lnk.generate_key()

    lnk.commit()

    if lnk.type == DIRECT:
        try:
            loc = link.Location(
                link=lnk,
                name='server',
                type=DIRECT_SERVER,
                link_id=lnk.id,
            )
            loc.commit()

            loc = link.Location(
                link=lnk,
                name='client',
                type=DIRECT_CLIENT,
                link_id=lnk.id,
            )
            loc.commit()
        except:
            lnk.remove()
            raise

    event.Event(type=LINKS_UPDATED)

    return utils.jsonify(lnk.dict())

@app.app.route('/link/<link_id>', methods=['DELETE'])
@auth.session_auth
def link_delete(link_id):
    if not settings.local.sub_plan or \
            'enterprise' not in settings.local.sub_plan:
        return flask.abort(404)

    if settings.app.demo_mode:
        return utils.demo_blocked()

    lnk = link.get_by_id(link_id)
    if not lnk:
        return flask.abort(404)

    lnk.remove()

    event.Event(type=LINKS_UPDATED)

    return utils.jsonify({})

@app.app.route('/link/<link_id>', methods=['PUT'])
@auth.session_auth
def link_put(link_id):
    if not settings.local.sub_plan or \
            'enterprise' not in settings.local.sub_plan:
        return flask.abort(404)

    if settings.app.demo_mode:
        return utils.demo_blocked()

    lnk = link.get_by_id(link_id)
    if not lnk:
        return flask.abort(404)

    lnk.name = utils.filter_str(flask.request.json.get('name')) or 'undefined'

    status = flask.request.json.get('status')
    if status in (ONLINE, OFFLINE):
        lnk.status = status

    if flask.request.json.get('key'):
        lnk.generate_key()

    lnk.ipv6 = True if flask.request.json.get('ipv6') else False

    if flask.request.json.get('protocol') == 'wg':
        lnk.protocol = 'wg'
    else:
        lnk.protocol = 'ipsec'

    lnk.wg_port = flask.request.json.get('wg_port')
    if not lnk.wg_port or lnk.wg_port < 1 or lnk.wg_port > 65535:
        lnk.wg_port = random.randint(30000, 32500)

    lnk.host_check = True if flask.request.json.get('host_check') else False

    lnk.action = RESTART if flask.request.json.get(
        'action') == RESTART else HOLD

    lnk.preferred_ike = utils.filter_str2(
        flask.request.json.get('preferred_ike')) or None
    lnk.preferred_esp = utils.filter_str2(
        flask.request.json.get('preferred_esp')) or None
    lnk.force_preferred = True if flask.request.json.get(
        'force_preferred') else False

    lnk.commit(('name', 'status', 'key', 'ipv6', 'protocol', 'wg_port',
        'host_check', 'action', 'preferred_ike', 'preferred_esp',
        'force_preferred'))

    event.Event(type=LINKS_UPDATED)

    return utils.jsonify(lnk.dict())

@app.app.route('/link/<link_id>/location', methods=['GET'])
@auth.session_auth
def link_location_get(link_id):
    if not settings.local.sub_plan or \
            'enterprise' not in settings.local.sub_plan:
        return flask.abort(404)

    if settings.app.demo_mode:
        resp = utils.demo_get_cache()
        if resp:
            return utils.jsonify(resp)

    lnk = link.get_by_id(link_id)
    if not lnk:
        return flask.abort(404)

    hosts_map = {}
    locations = []
    for location_dict in lnk.iter_locations_dict():
        for host in location_dict['hosts']:
            hosts_map[str(host['id'])] = '%s - %s' % (
                location_dict['name'], host['name'])
        locations.append(location_dict)

    for location in locations:
        for host in location['hosts']:
            if host.get('hosts'):
                for host_id, host_status in host['hosts'].items():
                    host_status['name'] = hosts_map.get(host_id) or host_id

    if settings.app.demo_mode:
        utils.demo_set_cache(locations)
    return utils.jsonify(locations)

@app.app.route('/link/<link_id>/location', methods=['POST'])
@auth.session_auth
def link_location_post(link_id):
    if not settings.local.sub_plan or \
            'enterprise' not in settings.local.sub_plan:
        return flask.abort(404)

    if settings.app.demo_mode:
        return utils.demo_blocked()

    lnk = link.get_by_id(link_id)
    if not lnk or lnk.type == DIRECT:
        return flask.abort(404)

    name = utils.filter_str(flask.request.json.get('name')) or 'undefined'

    loc = link.Location(
        link=lnk,
        name=name,
        link_id=lnk.id,
    )
    loc.commit()

    event.Event(type=LINKS_UPDATED)

    return utils.jsonify(loc.dict())

@app.app.route('/link/<link_id>/location/<location_id>', methods=['PUT'])
@auth.session_auth
def link_location_put(link_id, location_id):
    if not settings.local.sub_plan or \
            'enterprise' not in settings.local.sub_plan:
        return flask.abort(404)

    if settings.app.demo_mode:
        return utils.demo_blocked()

    lnk = link.get_by_id(link_id)
    if not lnk or lnk.type == DIRECT:
        return flask.abort(404)

    loc = lnk.get_location(location_id)
    if not loc:
        return flask.abort(404)

    loc.name = utils.filter_str(flask.request.json.get('name')) or 'undefined'

    loc.commit('name')

    event.Event(type=LINKS_UPDATED)

    return utils.jsonify(loc.dict())

@app.app.route('/link/<link_id>/location/<location_id>', methods=['DELETE'])
@auth.session_auth
def link_location_delete(link_id, location_id):
    if not settings.local.sub_plan or \
            'enterprise' not in settings.local.sub_plan:
        return flask.abort(404)

    if settings.app.demo_mode:
        return utils.demo_blocked()

    lnk = link.get_by_id(link_id)
    if not lnk or lnk.type == DIRECT:
        return flask.abort(404)

    loc = lnk.get_location(location_id)
    if not loc:
        return flask.abort(404)

    loc.remove()

    event.Event(type=LINKS_UPDATED)

    return utils.jsonify({})

@app.app.route('/link/<link_id>/location/<location_id>/route',
    methods=['POST'])
@auth.session_auth
def link_location_route_post(link_id, location_id):
    if not settings.local.sub_plan or \
            'enterprise' not in settings.local.sub_plan:
        return flask.abort(404)

    if settings.app.demo_mode:
        return utils.demo_blocked()

    lnk = link.get_by_id(link_id)
    if not lnk or lnk.type == DIRECT:
        return flask.abort(404)

    loc = lnk.get_location(location_id)
    if not loc:
        return flask.abort(404)

    try:
        network = loc.add_route(flask.request.json.get('network'))
    except NetworkInvalid:
        return utils.jsonify({
            'error': LINK_NETWORK_INVALID,
            'error_msg': LINK_NETWORK_INVALID_MSG,
        }, 400)

    loc.commit('routes')

    event.Event(type=LINKS_UPDATED)

    return utils.jsonify({
        'id': network,
    })

@app.app.route('/link/<link_id>/location/<location_id>/route/<network>',
    methods=['DELETE'])
@auth.session_auth
def link_location_route_delete(link_id, location_id, network):
    if not settings.local.sub_plan or \
            'enterprise' not in settings.local.sub_plan:
        return flask.abort(404)

    if settings.app.demo_mode:
        return utils.demo_blocked()

    lnk = link.get_by_id(link_id)
    if not lnk or lnk.type == DIRECT:
        return flask.abort(404)

    loc = lnk.get_location(location_id)
    if not loc:
        return flask.abort(404)

    loc.remove_route(network)

    loc.commit('routes')

    event.Event(type=LINKS_UPDATED)

    return utils.jsonify({})

@app.app.route('/link/<link_id>/location/<location_id>/host',
    methods=['POST'])
@auth.session_auth
def link_location_host_post(link_id, location_id):
    if not settings.local.sub_plan or \
            'enterprise' not in settings.local.sub_plan:
        return flask.abort(404)

    if settings.app.demo_mode:
        return utils.demo_blocked()

    lnk = link.get_by_id(link_id)
    if not lnk:
        return flask.abort(404)

    loc = lnk.get_location(location_id)
    if not loc:
        return flask.abort(404)

    name = utils.filter_str(flask.request.json.get('name')) or 'undefined'
    timeout = int(flask.request.json.get('timeout') or 0) or None
    priority = abs(int(flask.request.json.get('priority') or 1)) or 1
    backoff = int(flask.request.json.get('backoff') or 0) or None
    static = bool(flask.request.json.get('static'))
    public_address = utils.filter_str(
        flask.request.json.get('public_address'))
    local_address = utils.filter_str(
        flask.request.json.get('local_address'))
    wg_public_key = utils.filter_base64(
        flask.request.json.get('wg_public_key'))

    hst = link.Host(
        link=lnk,
        location=loc,
        link_id=lnk.id,
        location_id=loc.id,
        name=name,
        timeout=timeout,
        priority=priority,
        backoff=backoff,
        static=static,
        public_address=public_address,
        local_address=local_address,
        wg_public_key=wg_public_key,
    )

    hst.generate_secret()

    hst.commit()

    event.Event(type=LINKS_UPDATED)

    return utils.jsonify(hst.dict())

@app.app.route('/link/<link_id>/location/<location_id>/host/<host_id>/uri',
    methods=['GET'])
@auth.session_auth
def link_location_host_uri_get(link_id, location_id, host_id):
    if not settings.local.sub_plan or \
            'enterprise' not in settings.local.sub_plan:
        return flask.abort(404)

    if settings.app.demo_mode:
        return utils.demo_blocked()

    lnk = link.get_by_id(link_id)
    if not lnk:
        return flask.abort(404)

    loc = lnk.get_location(location_id)
    if not loc:
        return flask.abort(404)

    hst = loc.get_host(host_id)
    if not hst:
        return flask.abort(404)

    data = hst.dict()
    data['uri'] = hst.get_uri()

    return utils.jsonify(data)

@app.app.route('/link/<link_id>/location/<location_id>/host/<host_id>/conf',
    methods=['GET'])
@auth.session_auth
def link_location_host_conf_get(link_id, location_id, host_id):
    if not settings.local.sub_plan or \
            'enterprise' not in settings.local.sub_plan:
        return flask.abort(404)

    if settings.app.demo_mode:
        return utils.demo_blocked()

    lnk = link.get_by_id(link_id)
    if not lnk:
        return flask.abort(404)

    loc = lnk.get_location(location_id)
    if not loc:
        return flask.abort(404)

    hst = loc.get_host(host_id)
    if not hst:
        return flask.abort(404)

    data = hst.dict()
    data['conf'] = hst.get_static_conf()
    data['ubnt_conf'] = hst.get_ubnt_conf()

    return utils.jsonify(data)

@app.app.route('/link/<link_id>/location/<location_id>/host/<host_id>',
    methods=['PUT'])
@auth.session_auth
def link_location_host_put(link_id, location_id, host_id):
    if not settings.local.sub_plan or \
            'enterprise' not in settings.local.sub_plan:
        return flask.abort(404)

    if settings.app.demo_mode:
        return utils.demo_blocked()

    lnk = link.get_by_id(link_id)
    if not lnk:
        return flask.abort(404)

    loc = lnk.get_location(location_id)
    if not loc:
        return flask.abort(404)

    hst = loc.get_host(host_id)
    if not hst:
        return flask.abort(404)

    hst.name = utils.filter_str(flask.request.json.get('name')) or 'undefined'
    hst.timeout = abs(int(flask.request.json.get('timeout') or 0)) or None
    hst.priority = abs(int(flask.request.json.get('priority') or 1)) or 1
    hst.backoff = abs(int(flask.request.json.get('backoff') or 0)) or None
    hst.static = bool(flask.request.json.get('static'))
    hst.public_address = utils.filter_str(
        flask.request.json.get('public_address'))
    hst.local_address = utils.filter_str(
        flask.request.json.get('local_address'))

    hst.commit(('name', 'timeout', 'priority', 'backoff', 'static',
        'public_address', 'local_address'))

    event.Event(type=LINKS_UPDATED)

    return utils.jsonify(hst.dict())

@app.app.route('/link/<link_id>/location/<location_id>/host/<host_id>',
    methods=['DELETE'])
@auth.session_auth
def link_location_host_delete(link_id, location_id, host_id):
    if not settings.local.sub_plan or \
            'enterprise' not in settings.local.sub_plan:
        return flask.abort(404)

    if settings.app.demo_mode:
        return utils.demo_blocked()

    lnk = link.get_by_id(link_id)
    if not lnk:
        return flask.abort(404)

    loc = lnk.get_location(location_id)
    if not loc:
        return flask.abort(404)

    hst = loc.get_host(host_id)
    if not hst:
        return flask.abort(404)

    hst.remove()

    event.Event(type=LINKS_UPDATED)

    return utils.jsonify({})

@app.app.route('/link/<link_id>/location/<location_id>/peer',
    methods=['POST'])
@auth.session_auth
def link_location_peer_post(link_id, location_id):
    if not settings.local.sub_plan or \
            'enterprise' not in settings.local.sub_plan:
        return flask.abort(404)

    if settings.app.demo_mode:
        return utils.demo_blocked()

    lnk = link.get_by_id(link_id)
    if not lnk or lnk.type == DIRECT:
        return flask.abort(404)

    loc = lnk.get_location(location_id)
    if not loc:
        return flask.abort(404)

    peer_id = database.ParseObjectId(flask.request.json.get('peer_id'))
    loc.remove_exclude(peer_id)

    lnk.commit('excludes')
    loc.commit('transit_excludes')

    event.Event(type=LINKS_UPDATED)

    return utils.jsonify({})

@app.app.route('/link/<link_id>/location/<location_id>/peer/<peer_id>',
    methods=['DELETE'])
@auth.session_auth
def link_location_peer_delete(link_id, location_id, peer_id):
    if not settings.local.sub_plan or \
            'enterprise' not in settings.local.sub_plan:
        return flask.abort(404)

    if settings.app.demo_mode:
        return utils.demo_blocked()

    lnk = link.get_by_id(link_id)
    if not lnk or lnk.type == DIRECT:
        return flask.abort(404)

    loc = lnk.get_location(location_id)
    if not loc:
        return flask.abort(404)

    loc.add_exclude(peer_id)

    lnk.commit('excludes')
    loc.commit('transit_excludes')

    event.Event(type=LINKS_UPDATED)

    return utils.jsonify({})

@app.app.route('/link/<link_id>/location/<location_id>/transit',
    methods=['POST'])
@auth.session_auth
def link_location_transit_post(link_id, location_id):
    if not settings.local.sub_plan or \
            'enterprise' not in settings.local.sub_plan:
        return flask.abort(404)

    if settings.app.demo_mode:
        return utils.demo_blocked()

    lnk = link.get_by_id(link_id)
    if not lnk or lnk.type == DIRECT:
        return flask.abort(404)

    loc = lnk.get_location(location_id)
    if not loc:
        return flask.abort(404)

    transit_id = database.ParseObjectId(flask.request.json.get('transit_id'))
    loc.add_transit(transit_id)

    loc.commit('transits')

    event.Event(type=LINKS_UPDATED)

    return utils.jsonify({})

@app.app.route('/link/<link_id>/location/<location_id>/transit/<transit_id>',
    methods=['DELETE'])
@auth.session_auth
def link_location_transit_delete(link_id, location_id, transit_id):
    if not settings.local.sub_plan or \
            'enterprise' not in settings.local.sub_plan:
        return flask.abort(404)

    if settings.app.demo_mode:
        return utils.demo_blocked()

    lnk = link.get_by_id(link_id)
    if not lnk or lnk.type == DIRECT:
        return flask.abort(404)

    loc = lnk.get_location(location_id)
    if not loc:
        return flask.abort(404)

    loc.remove_transit(transit_id)

    loc.commit('transits')

    event.Event(type=LINKS_UPDATED)

    return utils.jsonify({})

@app.app.route('/link/state', methods=['PUT'])
@auth.open_auth
def link_state_put():
    if settings.app.demo_mode:
        return utils.demo_blocked()

    auth_token = flask.request.headers.get('Auth-Token', None)
    auth_timestamp = flask.request.headers.get('Auth-Timestamp', None)
    auth_nonce = flask.request.headers.get('Auth-Nonce', None)
    auth_signature = flask.request.headers.get('Auth-Signature', None)
    if not auth_token or not auth_timestamp or not auth_nonce or \
            not auth_signature:
        return flask.abort(406)
    auth_token = auth_token[:256]
    auth_timestamp = auth_timestamp[:64]
    auth_nonce = auth_nonce[:32]
    auth_signature = auth_signature[:512]

    try:
        if abs(int(auth_timestamp) - int(utils.time_now())) > \
                settings.app.auth_time_window:
            return flask.abort(408)
    except ValueError:
        return flask.abort(405)

    host = link.get_host(database.ObjectId(auth_token))
    if not host:
        return flask.abort(404)

    auth_string = '&'.join([
        auth_token,
        auth_timestamp,
        auth_nonce,
        flask.request.method,
        flask.request.path,
    ])

    if len(auth_string) > AUTH_SIG_STRING_MAX_LEN:
        return flask.abort(413)

    if not host.secret:
        raise ValueError('Host secret undefined')

    auth_test_signature = base64.b64encode(hmac.new(
        host.secret.encode(), auth_string.encode(),
        hashlib.sha512).digest()).decode()
    if not utils.const_compare(auth_signature, auth_test_signature):
        return flask.abort(401)

    nonces_collection = mongo.get_collection('auth_nonces')
    try:
        nonces_collection.insert_one({
            'token': auth_token,
            'nonce': auth_nonce,
            'timestamp': utils.now(),
        })
    except pymongo.errors.DuplicateKeyError:
        return flask.abort(409)

    host.load_link()

    req_timestamp = flask.request.json.get('timestamp') or int(auth_timestamp)
    host.version = flask.request.json.get('version')
    host.public_address = flask.request.json.get('public_address')
    host.local_address = flask.request.json.get('local_address')
    host.address6 = flask.request.json.get('address6')
    host.wg_public_key = flask.request.json.get('wg_public_key')
    if flask.request.json.get('hosts'):
        host.hosts = flask.request.json.get('hosts')

        processed = False
        if host.hosts_hist_timestamp:
            if req_timestamp in host.hosts_hist_timestamp:
                processed = True
            else:
                host.hosts_hist_timestamp.insert(0, req_timestamp)
                host.hosts_hist_timestamp = host.hosts_hist_timestamp[:6]
        else:
            host.hosts_hist_timestamp = [req_timestamp]

        if not processed:
            if host.hosts_hist:
                host.hosts_hist.insert(0, flask.request.json.get('hosts'))
                host.hosts_hist = host.hosts_hist[:6]
            else:
                host.hosts_hist = [flask.request.json.get('hosts')]
    else:
        host.hosts = None
        host.hosts_hist = None

    state, active = host.get_state()
    if active:
        host.location.status = flask.request.json.get('status') or None
        host.location.commit('status')

    data = json.dumps(state, default=lambda x: str(x))
    data += (16 - len(data) % 16) * '\x00'

    iv = os.urandom(16)
    key = hashlib.sha256(host.secret.encode()).digest()
    cipher = Cipher(
        algorithms.AES(key),
        modes.CBC(iv),
        backend=default_backend()
    ).encryptor()
    enc_data = base64.b64encode(cipher.update(
        data.encode()) + cipher.finalize())

    enc_signature = base64.b64encode(hmac.new(
        host.secret.encode(), enc_data,
        hashlib.sha512).digest()).decode()

    resp = flask.Response(response=enc_data, mimetype='application/base64')
    resp.headers.add('Cache-Control', 'no-cache, no-store, must-revalidate')
    resp.headers.add('Pragma', 'no-cache')
    resp.headers.add('Expires', 0)
    resp.headers.add('Cipher-IV', base64.b64encode(iv).decode())
    resp.headers.add('Cipher-Signature', enc_signature)

    return resp

@app.app.route('/link/state', methods=['DELETE'])
@auth.open_auth
def link_state_delete():
    if settings.app.demo_mode:
        return utils.demo_blocked()

    auth_token = flask.request.headers.get('Auth-Token', None)
    auth_timestamp = flask.request.headers.get('Auth-Timestamp', None)
    auth_nonce = flask.request.headers.get('Auth-Nonce', None)
    auth_signature = flask.request.headers.get('Auth-Signature', None)
    if not auth_token or not auth_timestamp or not auth_nonce or \
            not auth_signature:
        return flask.abort(406)
    auth_token = auth_token[:256]
    auth_timestamp = auth_timestamp[:64]
    auth_nonce = auth_nonce[:32]
    auth_signature = auth_signature[:512]

    try:
        if abs(int(auth_timestamp) - int(utils.time_now())) > \
                settings.app.auth_time_window:
            return flask.abort(408)
    except ValueError:
        return flask.abort(405)

    host = link.get_host(database.ObjectId(auth_token))
    if not host:
        return flask.abort(404)

    auth_string = '&'.join([
        auth_token,
        auth_timestamp,
        auth_nonce,
        flask.request.method,
        flask.request.path,
    ])

    if len(auth_string) > AUTH_SIG_STRING_MAX_LEN:
        return flask.abort(413)

    auth_test_signature = base64.b64encode(hmac.new(
        host.secret.encode(), auth_string.encode(),
        hashlib.sha512).digest()).decode()
    if not utils.const_compare(auth_signature, auth_test_signature):
        return flask.abort(401)

    nonces_collection = mongo.get_collection('auth_nonces')
    try:
        nonces_collection.insert_one({
            'token': auth_token,
            'nonce': auth_nonce,
            'timestamp': utils.now(),
        })
    except pymongo.errors.DuplicateKeyError:
        return flask.abort(409)

    host.set_inactive()

    return utils.jsonify({})
