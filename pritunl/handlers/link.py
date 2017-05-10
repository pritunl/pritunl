from pritunl.constants import *
from pritunl import app
from pritunl import auth
from pritunl import settings
from pritunl import utils
from pritunl import mongo
from pritunl import link

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
    page = flask.request.args.get('page', None)
    page = int(page) if page else page

    links = []
    for lnk in link.iter_links(page):
        links.append(lnk.dict())

    return utils.jsonify({
        'page': page,
        'page_total': link.get_page_total(),
        'links': links,
    })

@app.app.route('/link/state', methods=['PUT'])
@auth.open_auth
def link_state_put():
    auth_token = flask.request.headers.get('Auth-Token', None)
    auth_timestamp = flask.request.headers.get('Auth-Timestamp', None)
    auth_nonce = flask.request.headers.get('Auth-Nonce', None)
    auth_signature = flask.request.headers.get('Auth-Signature', None)
    if not auth_token or not auth_timestamp or not auth_nonce or \
            not auth_signature:
        return flask.abort(401)
    auth_nonce = auth_nonce[:32]

    try:
        if abs(int(auth_timestamp) - int(utils.time_now())) > \
                settings.app.auth_time_window:
            return flask.abort(401)
    except ValueError:
        return flask.abort(401)

    host = link.get_host(utils.ObjectId(auth_token))
    if not host:
        return flask.abort(401)

    auth_string = '&'.join([
        auth_token,
        auth_timestamp,
        auth_nonce,
        flask.request.method,
        flask.request.path,
    ])

    if len(auth_string) > AUTH_SIG_STRING_MAX_LEN:
        return flask.abort(401)

    auth_test_signature = base64.b64encode(hmac.new(
        host.secret.encode(), auth_string,
        hashlib.sha512).digest())
    if auth_signature != auth_test_signature:
        return flask.abort(401)

    nonces_collection = mongo.get_collection('auth_nonces')
    try:
        nonces_collection.insert({
            'token': auth_token,
            'nonce': auth_nonce,
            'timestamp': utils.now(),
        })
    except pymongo.errors.DuplicateKeyError:
        return flask.abort(401)

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

    resp = flask.Response(response=enc_data, mimetype='application/base64')
    resp.headers.add('Cache-Control',
        'no-cache, no-store, must-revalidate')
    resp.headers.add('Pragma', 'no-cache')
    resp.headers.add('Expires', 0)
    resp.headers.add('Cipher-IV', base64.b64encode(iv))

    return resp
