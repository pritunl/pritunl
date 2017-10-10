from pritunl.constants import *
from pritunl.exceptions import *
from pritunl import app
from pritunl import auth
from pritunl import settings
from pritunl import utils
from pritunl import mongo
from pritunl import link
from pritunl import event

import pymongo
import flask
import base64
import hmac
import hashlib
import json
import Crypto.Random
import Crypto.Cipher.AES

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

    lnk = link.Link(
        name=name,
        status=ONLINE,
    )

    lnk.generate_key()

    lnk.commit()

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

    lnk.commit(('name', 'status', 'key'))

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

    locations = []
    for location_dict in lnk.iter_locations_dict():
        locations.append(location_dict)

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
    if not lnk:
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
    if not lnk:
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
    if not lnk:
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
    if not lnk:
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
    if not lnk:
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
    static = bool(flask.request.json.get('static'))
    public_address = utils.filter_str(
        flask.request.json.get('public_address'))

    hst = link.Host(
        link=lnk,
        location=loc,
        link_id=lnk.id,
        location_id=loc.id,
        name=name,
        timeout=timeout,
        priority=priority,
        static=static,
        public_address=public_address,
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
    hst.static = bool(flask.request.json.get('static'))
    hst.public_address = utils.filter_str(
        flask.request.json.get('public_address'))

    hst.commit(('name', 'timeout', 'priority', 'static', 'public_address'))

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

@app.app.route('/link/<link_id>/location/<location_id>/exclude',
    methods=['POST'])
@auth.session_auth
def link_location_exclude_post(link_id, location_id):
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

    exclude_id = utils.ObjectId(flask.request.json.get('exclude_id'))
    loc.add_exclude(exclude_id)

    lnk.commit('excludes')

    event.Event(type=LINKS_UPDATED)

    return utils.jsonify({
        'location_id': exclude_id,
    })

@app.app.route('/link/<link_id>/location/<location_id>/exclude/<exclude_id>',
    methods=['DELETE'])
@auth.session_auth
def link_location_exclude_delete(link_id, location_id, exclude_id):
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

    loc.remove_exclude(exclude_id)

    lnk.commit('excludes')

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
    auth_nonce = auth_nonce[:32]

    try:
        if abs(int(auth_timestamp) - int(utils.time_now())) > \
                settings.app.auth_time_window:
            return flask.abort(408)
    except ValueError:
        return flask.abort(405)

    host = link.get_host(utils.ObjectId(auth_token))
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
        host.secret.encode(), auth_string,
        hashlib.sha512).digest())
    if not utils.const_compare(auth_signature, auth_test_signature):
        return flask.abort(401)

    nonces_collection = mongo.get_collection('auth_nonces')
    try:
        nonces_collection.insert({
            'token': auth_token,
            'nonce': auth_nonce,
            'timestamp': utils.now(),
        })
    except pymongo.errors.DuplicateKeyError:
        return flask.abort(409)

    host.load_link()

    host.version = flask.request.json.get('version')
    host.public_address = flask.request.json.get('public_address')
    host.address6 = flask.request.json.get('address6')

    data = json.dumps(host.get_state(), default=lambda x: str(x))
    data += (16 - len(data) % 16) * '\x00'

    iv = Crypto.Random.new().read(16)
    key = hashlib.sha256(host.secret).digest()
    cipher = Crypto.Cipher.AES.new(
        key,
        Crypto.Cipher.AES.MODE_CBC,
        iv,
    )

    enc_data = base64.b64encode(cipher.encrypt(data))
    enc_signature = base64.b64encode(hmac.new(
        host.secret.encode(), enc_data,
        hashlib.sha512).digest())

    resp = flask.Response(response=enc_data, mimetype='application/base64')
    resp.headers.add('Cache-Control',
        'no-cache, no-store, must-revalidate')
    resp.headers.add('Pragma', 'no-cache')
    resp.headers.add('Expires', 0)
    resp.headers.add('Cipher-IV', base64.b64encode(iv))
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
    auth_nonce = auth_nonce[:32]

    try:
        if abs(int(auth_timestamp) - int(utils.time_now())) > \
                settings.app.auth_time_window:
            return flask.abort(408)
    except ValueError:
        return flask.abort(405)

    host = link.get_host(utils.ObjectId(auth_token))
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
        host.secret.encode(), auth_string,
        hashlib.sha512).digest())
    if not utils.const_compare(auth_signature, auth_test_signature):
        return flask.abort(401)

    nonces_collection = mongo.get_collection('auth_nonces')
    try:
        nonces_collection.insert({
            'token': auth_token,
            'nonce': auth_nonce,
            'timestamp': utils.now(),
        })
    except pymongo.errors.DuplicateKeyError:
        return flask.abort(409)

    host.set_inactive()

    return utils.jsonify({})
