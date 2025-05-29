from pritunl.constants import *
from pritunl.exceptions import *
from pritunl import utils
from pritunl import static
from pritunl import organization
from pritunl import user
from pritunl import server
from pritunl import settings
from pritunl import app
from pritunl import auth
from pritunl import mongo
from pritunl import sso
from pritunl import event
from pritunl import logger
from pritunl import limiter
from pritunl import journal
from pritunl import messenger

import flask
import time
import pymongo
import hmac
import hashlib
import base64
import datetime
import threading
import urllib.parse
import requests
import json
import unicodedata
import ipaddress
import nacl.public
from cryptography.exceptions import InvalidSignature

def _get_key_tar_archive(org_id, user_id):
    org = organization.get_by_id(org_id)
    usr = org.get_user(user_id)
    key_archive = usr.build_key_tar_archive()
    response = flask.Response(response=key_archive,
        mimetype='application/octet-stream')
    response.headers.add('Content-Disposition',
        'attachment; filename="%s.tar"' %
        unicodedata.normalize(
            'NFKD', usr.name).encode('ascii', 'ignore').decode())
    return (usr, response)

def _get_key_zip_archive(org_id, user_id):
    org = organization.get_by_id(org_id)
    usr = org.get_user(user_id)
    key_archive = usr.build_key_zip_archive()
    response = flask.Response(response=key_archive,
        mimetype='application/octet-stream')
    response.headers.add('Content-Disposition',
        'attachment; filename="%s_%s.zip"' % (
            unicodedata.normalize(
                'NFKD', org.name).encode('ascii', 'ignore').decode(),
            unicodedata.normalize(
                'NFKD', usr.name).encode('ascii', 'ignore').decode(),
        ))
    return (usr, response)

def _get_onc_archive(org_id, user_id):
    org = organization.get_by_id(org_id)
    usr = org.get_user(user_id)
    onc_conf = usr.build_onc()
    response = flask.Response(response=onc_conf,
        mimetype='application/x-onc')
    response.headers.add('Content-Disposition',
        'attachment; filename="%s_%s.onc"' % (
            unicodedata.normalize(
                'NFKD', org.name).encode('ascii', 'ignore').decode(),
            unicodedata.normalize(
                'NFKD', usr.name).encode('ascii', 'ignore').decode(),
        ))
    return (usr, response)

def _find_doc(query, one_time=None, one_time_new=False):
    utils.rand_sleep()

    collection = mongo.get_collection('users_key_link')
    doc = collection.find_one(query)

    if one_time and doc and doc.get('one_time'):
        if utils.now() - doc['timestamp'] > datetime.timedelta(
                seconds=settings.app.key_link_timeout_short):
            return None

        short_id = utils.rand_str(settings.app.long_url_length)
        collection = mongo.get_collection('users_key_link')

        if one_time_new:
            set_doc = {
                'short_id': short_id,
            }
        else:
            set_doc = {
                'one_time': 'used',
            }

        response = collection.update_one({
            '_id': doc['_id'],
            'short_id': doc['short_id'],
            'one_time': True,
        }, {'$set': set_doc})
        if not bool(response.modified_count):
            return None

        if one_time_new:
            doc['short_id'] = short_id

    if not doc:
        time.sleep(settings.app.rate_limit_sleep)

    return doc

@app.app.route('/key/<org_id>/<user_id>.tar', methods=['GET'])
@auth.session_light_auth
def user_key_tar_archive_get(org_id, user_id):
    remote_addr = utils.get_remote_addr()
    usr, resp = _get_key_tar_archive(org_id, user_id)

    usr.audit_event('user_profile',
        'User tar profile downloaded from web console',
        remote_addr=remote_addr,
    )

    journal.entry(
        journal.USER_PROFILE_SUCCESS,
        usr.journal_data,
        remote_address=remote_addr,
        event_long='User tar profile downloaded from web console',
    )

    return resp

@app.app.route('/key/<org_id>/<user_id>.zip', methods=['GET'])
@auth.session_light_auth
def user_key_zip_archive_get(org_id, user_id):
    remote_addr = utils.get_remote_addr()
    usr, resp = _get_key_zip_archive(org_id, user_id)

    usr.audit_event('user_profile',
        'User zip profile downloaded from web console',
        remote_addr=remote_addr,
    )

    journal.entry(
        journal.USER_PROFILE_SUCCESS,
        usr.journal_data,
        remote_address=remote_addr,
        event_long='User zip profile downloaded from web console',
    )

    return resp

@app.app.route('/key_onc/<org_id>/<user_id>.onc', methods=['GET'])
@auth.session_light_auth
def user_key_onc_archive_get(org_id, user_id):
    remote_addr = utils.get_remote_addr()
    usr, resp = _get_onc_archive(org_id, user_id)

    usr.audit_event('user_profile',
        'User onc profile downloaded from web console',
        remote_addr=remote_addr,
    )

    journal.entry(
        journal.USER_PROFILE_SUCCESS,
        usr.journal_data,
        remote_address=remote_addr,
        event_long='User onc profile downloaded from web console',
    )

    return resp

@app.app.route('/key/<org_id>/<user_id>', methods=['GET'])
@auth.session_auth
def user_key_link_get(org_id, user_id):
    remote_addr = utils.get_remote_addr()
    org = organization.get_by_id(org_id)
    usr = org.get_user(user_id)

    usr.audit_event('user_profile',
        'User temporary profile links created from web console',
        remote_addr=remote_addr,
    )

    journal.entry(
        journal.USER_PROFILE_SUCCESS,
        usr.journal_data,
        remote_address=remote_addr,
        event_long='User temporary profile links created from web console',
    )

    return utils.jsonify(org.create_user_key_link(user_id))

@app.app.route('/key/<org_id>/<user_id>/<server_id>.key', methods=['GET'])
@auth.session_light_auth
def user_linked_key_conf_get(org_id, user_id, server_id):
    remote_addr = utils.get_remote_addr()
    org = organization.get_by_id(org_id)
    usr = org.get_user(user_id)
    key_conf = usr.build_key_conf(server_id)

    usr.audit_event('user_profile',
        'User key profile downloaded from web console',
        remote_addr=remote_addr,
    )

    journal.entry(
        journal.USER_PROFILE_SUCCESS,
        usr.journal_data,
        remote_address=remote_addr,
        event_long='User key profile downloaded from web console',
    )

    response = flask.Response(response=key_conf['conf'],
        mimetype='application/ovpn')
    response.headers.add('Content-Disposition',
        'attachment; filename="%s"' % key_conf['name'])

    return response

@app.app.route('/key/<key_id>.tar', methods=['GET'])
@auth.open_auth
def user_linked_key_tar_archive_get(key_id):
    key_id = key_id[:128]
    remote_addr = utils.get_remote_addr()
    doc = _find_doc({
        'key_id': key_id,
    })
    if not doc:
        journal.entry(
            journal.USER_PROFILE_FAILURE,
            remote_address=remote_addr,
            event_long='Key ID not found',
        )
        return flask.abort(404)

    if settings.user.restrict_import:
        return flask.abort(404)

    usr, resp = _get_key_tar_archive(doc['org_id'], doc['user_id'])
    if usr.disabled:
        journal.entry(
            journal.USER_PROFILE_FAILURE,
            usr.journal_data,
            remote_address=remote_addr,
            event_long='User disabled',
        )
        return flask.abort(403)

    journal.entry(
        journal.USER_PROFILE_SUCCESS,
        usr.journal_data,
        remote_address=remote_addr,
        event_long='User tar profile downloaded with temporary profile link',
    )

    usr.audit_event('user_profile',
        'User tar profile downloaded with temporary profile link',
        remote_addr=remote_addr,
    )

    return resp

@app.app.route('/key/<key_id>.zip', methods=['GET'])
@auth.open_auth
def user_linked_key_zip_archive_get(key_id):
    key_id = key_id[:128]
    remote_addr = utils.get_remote_addr()
    doc = _find_doc({
        'key_id': key_id,
    })
    if not doc:
        journal.entry(
            journal.USER_PROFILE_FAILURE,
            remote_address=remote_addr,
            event_long='Key ID not found',
        )
        return flask.abort(404)

    if settings.user.restrict_import:
        return flask.abort(404)

    usr, resp = _get_key_zip_archive(doc['org_id'], doc['user_id'])
    if usr.disabled:
        journal.entry(
            journal.USER_PROFILE_FAILURE,
            usr.journal_data,
            remote_address=remote_addr,
            event_long='User disabled',
        )
        return flask.abort(403)

    journal.entry(
        journal.USER_PROFILE_SUCCESS,
        usr.journal_data,
        remote_address=remote_addr,
        event_long='User zip profile downloaded with temporary profile link',
    )

    usr.audit_event('user_profile',
        'User zip profile downloaded with temporary profile link',
        remote_addr=remote_addr,
    )

    return resp

@app.app.route('/key_onc/<key_id>.onc', methods=['GET'])
@auth.open_auth
def user_linked_key_onc_archive_get(key_id):
    key_id = key_id[:128]
    remote_addr = utils.get_remote_addr()
    doc = _find_doc({
        'key_id': key_id,
    })
    if not doc:
        journal.entry(
            journal.USER_PROFILE_FAILURE,
            remote_address=remote_addr,
            event_long='Key ID not found',
        )
        return flask.abort(404)

    if settings.user.restrict_import:
        return flask.abort(404)

    usr, resp = _get_onc_archive(doc['org_id'], doc['user_id'])
    if usr.disabled:
        journal.entry(
            journal.USER_PROFILE_FAILURE,
            usr.journal_data,
            remote_address=remote_addr,
            event_long='User disabled',
        )
        return flask.abort(403)

    journal.entry(
        journal.USER_PROFILE_SUCCESS,
        usr.journal_data,
        remote_address=remote_addr,
        event_long='User onc profile downloaded with temporary profile link',
    )

    usr.audit_event('user_profile',
        'User onc profile downloaded with temporary profile link',
        remote_addr=remote_addr,
    )

    return resp

@app.app.route('/key_pin/<key_id>', methods=['PUT'])
@auth.open_auth
def user_key_pin_put(key_id):
    if settings.app.demo_mode:
        return utils.demo_blocked()

    key_id = key_id[:128]
    remote_addr = utils.get_remote_addr()

    doc = _find_doc({
        'key_id': key_id,
    })
    if not doc:
        journal.entry(
            journal.USER_PROFILE_FAILURE,
            remote_address=remote_addr,
            event_long='Key ID not found',
        )
        return flask.abort(404)

    if settings.user.pin_mode == PIN_DISABLED:
        return utils.jsonify({
            'error': PIN_IS_DISABLED,
            'error_msg': PIN_IS_DISABLED_MSG,
        }, 400)

    org = organization.get_by_id(doc['org_id'])
    usr = org.get_user(doc['user_id'])
    if usr.disabled:
        return flask.abort(403)

    if RADIUS_AUTH in usr.auth_type:
        return utils.jsonify({
            'error': PIN_RADIUS,
            'error_msg': PIN_RADIUS_MSG,
        }, 400)

    current_pin = utils.filter_str(
        flask.request.json.get('current_pin')) or None
    pin = utils.filter_str(flask.request.json.get('pin')) or None

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

    if usr.pin:
        if not limiter.auth_check(usr.id):
            return utils.jsonify({
                'error': AUTH_TOO_MANY,
                'error_msg': AUTH_TOO_MANY_MSG,
            }, 400)

        if not usr.check_pin(current_pin):
            return utils.jsonify({
                'error': PIN_INVALID,
                'error_msg': PIN_INVALID_MSG,
            }, 400)

    if usr.set_pin(pin):
        journal.entry(
            journal.USER_PIN_UPDATE,
            usr.journal_data,
            remote_address=remote_addr,
            event_long='User pin changed with temporary profile link',
        )

        usr.audit_event('user_updated',
            'User pin changed with temporary profile link',
            remote_addr=remote_addr,
        )

    usr.commit()

    event.Event(type=USERS_UPDATED, resource_id=org.id)

    return utils.jsonify({})

@app.app.route('/k/<short_code>', methods=['GET'])
@auth.open_auth
def user_linked_key_page_get(short_code):
    short_code = short_code[:128]
    remote_addr = utils.get_remote_addr()

    doc = _find_doc({
        'short_id': short_code,
    }, one_time=True, one_time_new=True)
    if not doc:
        journal.entry(
            journal.USER_PROFILE_FAILURE,
            remote_address=remote_addr,
            event_long='Key ID not found',
        )
        return flask.abort(404)

    org = organization.get_by_id(doc['org_id'])
    usr = org.get_user(id=doc['user_id'])
    if usr.disabled:
        journal.entry(
            journal.USER_PROFILE_FAILURE,
            usr.journal_data,
            remote_address=remote_addr,
            event_long='User disabled',
        )
        return flask.abort(403)

    journal.entry(
        journal.USER_PROFILE_SUCCESS,
        usr.journal_data,
        remote_address=remote_addr,
        event_long='User temporary profile link viewed',
    )

    usr.audit_event('user_profile',
        'User temporary profile link viewed',
        remote_addr=remote_addr,
    )

    if settings.local.sub_active and settings.app.theme == 'dark':
        view_name = KEY_VIEW_DARK_NAME
    else:
        view_name = KEY_VIEW_NAME

    if RADIUS_AUTH in usr.auth_type or \
            settings.user.pin_mode == PIN_DISABLED:
        header_class = 'pin-disabled'
    else:
        header_class = ''

    if settings.user.restrict_import:
        header_class += ' restrict-import'

    key_page = static.StaticFile(settings.conf.www_path, view_name,
        cache=False, gzip=False).data

    uri_url = (utils.get_url_root() + '/ku/' + doc['short_id'])
    if uri_url.startswith('https'):
        uri_url = uri_url.replace('https', 'pritunl', 1)
    else:
        uri_url = uri_url.replace('http', 'pritunl', 1)
    key_page = key_page.replace('<%= uri_url %>', uri_url)

    key_page = key_page.replace('<%= user_name %>', '%s - %s' % (
        org.name, usr.name))
    key_page = key_page.replace('<%= user_key_tar_url %>', '/key/%s.tar' % (
        doc['key_id']))
    key_page = key_page.replace('<%= user_key_zip_url %>', '/key/%s.zip' % (
        doc['key_id']))

    auth_modes = usr.get_auth_modes(org.otp_auth)

    if OTP_PASSCODE in auth_modes:
        key_page = key_page.replace('<%= user_otp_key %>', usr.otp_secret)
        key_page = key_page.replace('<%= user_otp_url %>',
            'otpauth://totp/%s@%s?secret=%s' % (
                urllib.parse.quote(usr.name),
                urllib.parse.quote(org.name),
                usr.otp_secret))
    else:
        key_page = key_page.replace('<%= user_otp_key %>', '')
        key_page = key_page.replace('<%= user_otp_url %>', '')

    if usr.pin:
        key_page = key_page.replace('<%= cur_pin_display %>', 'block')
    else:
        key_page = key_page.replace('<%= cur_pin_display %>', 'none')

    key_page = key_page.replace('<%= key_id %>', doc['key_id'])
    key_page = key_page.replace('<%= short_id %>', doc['short_id'])

    conf_links = ''

    if settings.local.sub_active:
        conf_links += '<a class="btn btn-success download-chrome" ' + \
            'title="Download Chrome OS Profile" ' + \
            'href="/key_onc/%s.onc">Download Chrome OS Profile</a>\n' % (
                doc['key_id'])

    has_servers = False
    for server in usr.iter_servers():
        has_servers = True
        conf_links += '<a class="btn btn-sm download-profile" ' + \
            'title="Download Profile" ' + \
            'href="/key/%s/%s.key">Download Profile (%s)</a>\n' % (
                doc['key_id'], server.id, server.name)
    key_page = key_page.replace('<%= conf_links %>', conf_links)

    if not has_servers:
        header_class += ' no-servers'
    key_page = key_page.replace('<%= header_class %>', header_class)

    return key_page

@app.app.route('/k/<short_code>', methods=['DELETE'])
@auth.open_auth
def user_linked_key_page_delete(short_code):
    utils.rand_sleep()
    short_code = short_code[:128]
    remote_addr = utils.get_remote_addr()

    journal.entry(
        journal.USER_PROFILE_DELETE,
        remote_address=remote_addr,
        event_long='Temporary profile link deleted',
    )

    collection = mongo.get_collection('users_key_link')
    collection.delete_one({
        'short_id': short_code,
    })

    return utils.jsonify({})

@app.app.route('/ku/<short_code>', methods=['GET'])
@auth.open_auth
def user_uri_key_page_get(short_code):
    short_code = short_code[:128]
    remote_addr = utils.get_remote_addr()

    doc = _find_doc({
        'short_id': short_code,
    }, one_time=True)
    if not doc:
        return flask.abort(404)

    org = organization.get_by_id(doc['org_id'])
    usr = org.get_user(id=doc['user_id'])
    if usr.disabled:
        return flask.abort(403)

    journal.entry(
        journal.USER_PROFILE_SUCCESS,
        usr.journal_data,
        remote_address=remote_addr,
        event_long='User temporary profile downloaded from pritunl client',
    )

    usr.audit_event('user_profile',
        'User temporary profile downloaded from pritunl client',
        remote_addr=remote_addr,
    )

    keys = {}
    for server in usr.iter_servers():
        key = usr.build_key_conf(server.id)
        keys[key['name']] = key['conf']

    return utils.jsonify(keys)

@app.app.route('/key/<key_id>/<server_id>.key', methods=['GET'])
@auth.open_auth
def user_linked_key_conf_get(key_id, server_id):
    key_id = key_id[:128]
    server_id = server_id
    remote_addr = utils.get_remote_addr()

    doc = _find_doc({
        'key_id': key_id,
    })
    if not doc:
        journal.entry(
            journal.USER_PROFILE_FAILURE,
            remote_address=remote_addr,
            event_long='Key ID not found',
        )
        return flask.abort(404)

    if settings.user.restrict_import:
        return flask.abort(404)

    org = organization.get_by_id(doc['org_id'])
    if not org:
        journal.entry(
            journal.USER_PROFILE_FAILURE,
            remote_address=remote_addr,
            event_long='Organization not found',
        )
        return flask.abort(404)

    usr = org.get_user(id=doc['user_id'])
    if not usr:
        journal.entry(
            journal.USER_PROFILE_FAILURE,
            remote_address=remote_addr,
            event_long='User not found',
        )
        return flask.abort(404)

    if usr.disabled:
        journal.entry(
            journal.USER_PROFILE_FAILURE,
            usr.journal_data,
            remote_address=remote_addr,
            event_long='User disabled',
        )
        return flask.abort(403)

    key_conf = usr.build_key_conf(server_id)

    journal.entry(
        journal.USER_PROFILE_SUCCESS,
        usr.journal_data,
        remote_address=remote_addr,
        event_long='User profile downloaded with temporary profile link',
    )

    usr.audit_event('user_profile',
        'User profile downloaded with temporary profile link',
        remote_addr=remote_addr,
    )

    response = flask.Response(response=key_conf['conf'],
        mimetype='application/ovpn')
    response.headers.add('Content-Disposition',
        'attachment; filename="%s"' % key_conf['name'])

    return response

@app.app.route('/key/sync/<org_id>/<user_id>/<server_id>/<key_hash>',
    methods=['GET'])
@auth.open_auth
def key_sync_get(org_id, user_id, server_id, key_hash):
    org_id = org_id
    user_id = user_id
    server_id = server_id
    key_hash = key_hash[:256]
    remote_addr = utils.get_remote_addr()

    if not settings.user.conf_sync:
        return utils.jsonify({})

    if not settings.local.sub_active:
        return utils.jsonify({}, status_code=480)

    utils.rand_sleep()

    auth_token = flask.request.headers.get('Auth-Token', None)
    auth_timestamp = flask.request.headers.get('Auth-Timestamp', None)
    auth_nonce = flask.request.headers.get('Auth-Nonce', None)
    auth_signature = flask.request.headers.get('Auth-Signature', None)
    if not auth_token or not auth_timestamp or not auth_nonce or \
            not auth_signature:
        journal.entry(
            journal.USER_SYNC_FAILURE,
            remote_address=remote_addr,
            event_long='Missing auth header',
        )
        return flask.abort(406)
    auth_token = auth_token[:256]
    auth_timestamp = auth_timestamp[:64]
    auth_nonce = auth_nonce[:32]
    auth_signature = auth_signature[:512]

    try:
        if abs(int(auth_timestamp) - int(utils.time_now())) > \
                settings.app.auth_time_window:
            journal.entry(
                journal.USER_SYNC_FAILURE,
                remote_address=remote_addr,
                event_long='Expired auth timestamp',
            )
            return flask.abort(408)
    except ValueError:
        journal.entry(
            journal.USER_SYNC_FAILURE,
            remote_address=remote_addr,
            event_long='Invalid auth timestamp',
        )
        return flask.abort(405)

    org = organization.get_by_id(org_id)
    if not org:
        journal.entry(
            journal.USER_SYNC_FAILURE,
            remote_address=remote_addr,
            event_long='Organization not found',
        )
        return flask.abort(404)

    usr = org.get_user(id=user_id)
    if not usr:
        journal.entry(
            journal.USER_SYNC_FAILURE,
            remote_address=remote_addr,
            event_long='User not found',
        )
        return flask.abort(404)
    elif not usr.sync_secret:
        journal.entry(
            journal.USER_SYNC_FAILURE,
            usr.journal_data,
            remote_address=remote_addr,
            event_long='User missing sync secret',
        )
        return flask.abort(410)

    if auth_token != usr.sync_token:
        journal.entry(
            journal.USER_SYNC_FAILURE,
            usr.journal_data,
            remote_address=remote_addr,
            event_long='Sync token mismatch',
        )
        return flask.abort(410)

    if usr.disabled:
        journal.entry(
            journal.USER_SYNC_FAILURE,
            usr.journal_data,
            remote_address=remote_addr,
            event_long='User disabled',
        )
        return flask.abort(403)

    auth_string = '&'.join([
        usr.sync_token, auth_timestamp, auth_nonce, flask.request.method,
        flask.request.path])

    if len(auth_string) > AUTH_SIG_STRING_MAX_LEN:
        journal.entry(
            journal.USER_SYNC_FAILURE,
            usr.journal_data,
            remote_address=remote_addr,
            event_long='Auth string len limit exceeded',
        )
        return flask.abort(413)

    auth_test_signature = base64.b64encode(hmac.new(
        usr.sync_secret.encode(), auth_string.encode(),
        hashlib.sha512).digest()).decode()
    if not utils.const_compare(auth_signature, auth_test_signature):
        journal.entry(
            journal.USER_SYNC_FAILURE,
            usr.journal_data,
            remote_address=remote_addr,
            event_long='Sync signature mismatch',
        )
        return flask.abort(401)

    nonces_collection = mongo.get_collection('auth_nonces')
    try:
        nonces_collection.insert_one({
            'token': auth_token,
            'nonce': auth_nonce,
            'timestamp': utils.now(),
        })
    except pymongo.errors.DuplicateKeyError:
        journal.entry(
            journal.USER_SYNC_FAILURE,
            usr.journal_data,
            remote_address=remote_addr,
            event_long='Duplicate key',
        )
        return flask.abort(409)

    key_conf = usr.sync_conf(server_id, key_hash)
    if key_conf:
        usr.audit_event('user_profile',
            'User profile synced from pritunl client',
            remote_addr=remote_addr,
        )

        journal.entry(
            journal.USER_SYNC_SUCCESS,
            usr.journal_data,
            remote_address=remote_addr,
            event_long='User profile synced from pritunl client',
        )

        sync_signature = base64.b64encode(hmac.new(
            usr.sync_secret.encode(), key_conf['conf'].encode(),
            hashlib.sha512).digest()).decode()

        return utils.jsonify({
            'signature': sync_signature,
            'conf': key_conf['conf'],
        })

    return utils.jsonify({})

@app.app.route('/key/wg/<org_id>/<user_id>/<server_id>',
    methods=['POST'])
@auth.open_auth
def key_wg_post(org_id, user_id, server_id):
    org_id = org_id
    user_id = user_id
    server_id = server_id
    remote_addr = utils.get_remote_addr()

    auth_token = flask.request.headers.get('Auth-Token', None)
    auth_timestamp = flask.request.headers.get('Auth-Timestamp', None)
    auth_nonce = flask.request.headers.get('Auth-Nonce', None)
    auth_signature = flask.request.headers.get('Auth-Signature', None)
    if not auth_token or not auth_timestamp or not auth_nonce or \
            not auth_signature:
        journal.entry(
            journal.USER_WG_FAILURE,
            remote_address=remote_addr,
            event_long='Missing auth header',
        )
        return flask.abort(406)
    auth_token = auth_token[:256]
    auth_timestamp = auth_timestamp[:64]
    auth_nonce = auth_nonce[:32]
    auth_signature = auth_signature[:512]

    try:
        if abs(int(auth_timestamp) - int(utils.time_now())) > \
                settings.app.auth_time_window:
            journal.entry(
                journal.USER_WG_FAILURE,
                remote_address=remote_addr,
                event_long='Expired auth timestamp',
            )
            return flask.abort(408)
    except ValueError:
        journal.entry(
            journal.USER_WG_FAILURE,
            remote_address=remote_addr,
            event_long='Invalid auth timestamp',
        )
        return flask.abort(405)

    org = organization.get_by_id(org_id)
    if not org:
        journal.entry(
            journal.USER_WG_FAILURE,
            remote_address=remote_addr,
            event_long='Organization not found',
        )
        return flask.abort(404)

    usr = org.get_user(id=user_id)
    if not usr:
        journal.entry(
            journal.USER_WG_FAILURE,
            remote_address=remote_addr,
            event_long='User not found',
        )
        return flask.abort(404)
    elif not usr.sync_secret:
        journal.entry(
            journal.USER_WG_FAILURE,
            usr.journal_data,
            remote_address=remote_addr,
            event_long='User missing sync secret',
        )
        return flask.abort(410)

    if auth_token != usr.sync_token:
        journal.entry(
            journal.USER_WG_FAILURE,
            usr.journal_data,
            remote_address=remote_addr,
            event_long='Sync token mismatch',
        )
        return flask.abort(411)

    if usr.disabled:
        journal.entry(
            journal.USER_WG_FAILURE,
            usr.journal_data,
            remote_address=remote_addr,
            event_long='User disabled',
        )
        return flask.abort(403)

    cipher_data64 = flask.request.json.get('data')
    box_nonce64 = flask.request.json.get('nonce')
    public_key64 = flask.request.json.get('public_key')
    signature64 = flask.request.json.get('signature')
    device_signature64 = flask.request.json.get('device_signature')

    auth_string = '&'.join([
        usr.sync_token, auth_timestamp, auth_nonce, flask.request.method,
        flask.request.path, cipher_data64, box_nonce64, public_key64,
        signature64] + ([device_signature64] if device_signature64 else []))

    if len(auth_string) > AUTH_SIG_STRING_MAX_LEN:
        journal.entry(
            journal.USER_WG_FAILURE,
            usr.journal_data,
            remote_address=remote_addr,
            event_long='Auth string len limit exceeded',
        )
        return flask.abort(414)

    auth_test_signature = base64.b64encode(hmac.new(
        usr.sync_secret.encode(), auth_string.encode(),
        hashlib.sha512).digest()).decode()
    if not utils.const_compare(auth_signature, auth_test_signature):
        journal.entry(
            journal.USER_WG_FAILURE,
            usr.journal_data,
            remote_address=remote_addr,
            event_long='Auth signature mismatch',
        )
        return flask.abort(401)

    nonces_collection = mongo.get_collection('auth_nonces')
    try:
        nonces_collection.insert_one({
            'token': auth_token,
            'nonce': auth_nonce,
            'timestamp': utils.now(),
        })
    except pymongo.errors.DuplicateKeyError:
        journal.entry(
            journal.USER_WG_FAILURE,
            usr.journal_data,
            remote_address=remote_addr,
            event_long='Duplicate nonce from reconnection',
        )
        return flask.abort(409)

    data_hash = hashlib.sha512(
        '&'.join([cipher_data64, box_nonce64, public_key64]).encode(),
    ).digest()
    try:
        usr.verify_sig(
            data_hash,
            base64.b64decode(signature64),
        )
    except InvalidSignature:
        journal.entry(
            journal.USER_WG_FAILURE,
            usr.journal_data,
            remote_address=remote_addr,
            event_long='Invalid rsa signature',
        )
        return flask.abort(412)

    svr = usr.get_server(server_id)

    sender_pub_key = nacl.public.PublicKey(
        base64.b64decode(public_key64))
    box_nonce = base64.b64decode(box_nonce64)

    priv_key = nacl.public.PrivateKey(
        base64.b64decode(svr.auth_box_private_key))

    cipher_data = base64.b64decode(cipher_data64)
    nacl_box = nacl.public.Box(priv_key, sender_pub_key)
    plaintext = nacl_box.decrypt(cipher_data, box_nonce).decode()

    try:
        nonces_collection.insert_one({
            'token': auth_token,
            'nonce': box_nonce64,
            'timestamp': utils.now(),
        })
    except pymongo.errors.DuplicateKeyError:
        journal.entry(
            journal.USER_WG_FAILURE,
            usr.journal_data,
            remote_address=remote_addr,
            event_long='Duplicate secondary nonce',
        )
        return flask.abort(415)

    key_data = json.loads(plaintext)

    client_platform = utils.filter_str(key_data['platform'])
    client_ver = utils.filter_str(key_data.get('client_ver'))
    client_device_id = utils.filter_str(key_data['device_id'])
    client_device_name = utils.filter_str(key_data['device_name'])
    client_device_hostname = utils.filter_str(
        key_data.get('device_hostname')) or client_device_name
    client_device_key64 = utils.filter_str(key_data.get('device_key'))
    client_mac_addr = utils.filter_str(key_data['mac_addr'])
    client_mac_addrs = key_data['mac_addrs']
    if client_mac_addrs:
        client_mac_addrs = [utils.filter_str(x)
            for x in client_mac_addrs]
    else:
        client_mac_addrs = None
    client_auth_token = key_data['token']
    client_auth_nonce = utils.filter_str(key_data['nonce'])
    client_auth_password = key_data['password']
    client_auth_timestamp = int(key_data['timestamp'])
    client_public_address = utils.filter_str(
        key_data.get('public_address'))
    client_public_address6 = utils.filter_str(
        key_data.get('public_address6'))
    client_wg_public_key = key_data['wg_public_key']

    if client_public_address:
        client_public_address = str(ipaddress.IPv4Address(
            client_public_address))
    else:
        client_public_address = None

    if client_public_address6:
        client_public_address6 = str(ipaddress.IPv6Address(
            client_public_address6))
    else:
        client_public_address6 = None

    if ':' in remote_addr:
        remote_addr = str(ipaddress.IPv6Address(remote_addr))
    else:
        remote_addr = str(ipaddress.IPv4Address(remote_addr))

    if len(client_wg_public_key) < 32:
        journal.entry(
            journal.USER_WG_FAILURE,
            usr.journal_data,
            remote_address=remote_addr,
            event_long='Public key too short',
        )
        return flask.abort(416)

    try:
        client_wg_public_key = base64.b64decode(client_wg_public_key)
        if len(client_wg_public_key) != 32:
            raise ValueError('Invalid length')
        client_wg_public_key = base64.b64encode(
            client_wg_public_key).decode()
    except:
        journal.entry(
            journal.USER_WG_FAILURE,
            usr.journal_data,
            remote_address=remote_addr,
            event_long='Public key invalid',
        )
        return flask.abort(417)

    if svr.device_auth:
        if not client_device_key64 or not device_signature64:
            journal.entry(
                journal.USER_WG_FAILURE,
                usr.journal_data,
                remote_address=remote_addr,
                event_long='Invalid device signature',
            )
            return utils.jsonify({
                'error': 'device_signature_missing',
                'error_msg': 'Device signature missing.',
            }, 400)

        try:
            usr.device_verify_sig(
                client_device_hostname,
                client_platform,
                utils.base64raw_decode(client_device_key64),
                data_hash,
                utils.base64raw_decode(device_signature64),
            )

            journal.entry(
                journal.USER_DEVICE_AUTHENTICATE_SUCCESS,
                usr.journal_data,
                device_name=client_device_hostname,
                device_platform=client_platform,
                device_public_key=client_device_key64,
                remote_address=remote_addr,
                event_long='User verified device signature',
            )
        except DeviceUnregistered as err:
            send_data = {
                'allow': False,
                'token': None,
                'reason': None,
                'reg_key': err.reg_key,
                'remote': settings.local.host.public_addr,
                'remote6': settings.local.host.public_addr6,
            }

            send_nonce = nacl.utils.random(nacl.public.Box.NONCE_SIZE)
            nacl_box = nacl.public.Box(priv_key, sender_pub_key)
            send_cipher_data = nacl_box.encrypt(
                json.dumps(send_data).encode(), send_nonce)
            send_cipher_data = send_cipher_data[nacl.public.Box.NONCE_SIZE:]

            send_nonce64 = base64.b64encode(send_nonce).decode()
            send_cipher_data64 = base64.b64encode(send_cipher_data).decode()

            usr.audit_event('user_profile',
                'User device registration required',
                remote_addr=remote_addr,
            )

            journal.entry(
                journal.USER_DEVICE_CREATE,
                usr.journal_data,
                device_name=client_device_hostname,
                device_platform=client_platform,
                device_public_key=client_device_key64,
                remote_address=remote_addr,
                event_long='New user device request',
            )

            journal.entry(
                journal.USER_WG_FAILURE,
                usr.journal_data,
                remote_address=remote_addr,
                event_long='Device registration required',
            )

            sync_signature = base64.b64encode(hmac.new(
                usr.sync_secret.encode(),
                (send_cipher_data64 + '&' + send_nonce64).encode(),
                hashlib.sha512).digest()).decode()

            return utils.jsonify({
                'data': send_cipher_data64,
                'nonce': send_nonce64,
                'signature': sync_signature,
            })
        except InvalidSignature:
            journal.entry(
                journal.USER_DEVICE_AUTHENTICATE_FAILURE,
                usr.journal_data,
                device_name=client_device_name,
                device_platform=client_platform,
                device_public_key=client_device_key64,
                remote_address=remote_addr,
                event_long='User device signature invalid',
            )
            journal.entry(
                journal.USER_WG_FAILURE,
                usr.journal_data,
                device_name=client_device_name,
                device_platform=client_platform,
                device_public_key=client_device_key64,
                remote_address=remote_addr,
                event_long='Invalid device signature',
            )
            return utils.jsonify({
                'error': 'device_signature_invalid',
                'error_msg': 'Device signature invalid.',
            }, 400)

    instance = server.get_instance(server_id)
    if not instance or instance.state != 'running':
        return flask.abort(429)

    if not instance.server.wg:
        return flask.abort(429)

    if instance.server.sso_auth:
        return _key_request_init(org.id, usr.id, svr.id, 'wg')

    wg_keys_collection = mongo.get_collection('wg_keys')
    try:
        wg_keys_collection.insert_one({
            '_id': client_wg_public_key,
            'timestamp': utils.now(),
        })
    except pymongo.errors.DuplicateKeyError:
        journal.entry(
            journal.USER_WG_FAILURE,
            usr.journal_data,
            remote_address=remote_addr,
            wg_public_key=client_wg_public_key,
            event_long='Duplicate wg public key',
        )
        return flask.abort(413)

    clients = instance.instance_com.clients

    event = threading.Event()
    send_data = {
        'allow': None,
        'configuration': None,
        'reason': None,
    }
    def callback(allow, data):
        send_data['allow'] = allow
        if allow:
            send_data['configuration'] = data
        else:
            send_data['reason'] = data
        event.set()

    clients.connect_wg(
        user=usr,
        org=org,
        wg_public_key=client_wg_public_key,
        auth_password=client_auth_password,
        auth_token=client_auth_token,
        auth_nonce=client_auth_nonce,
        auth_timestamp=client_auth_timestamp,
        sso_token=None,
        platform=client_platform,
        client_ver=client_ver,
        device_id=client_device_id,
        device_name=client_device_name,
        mac_addr=client_mac_addr,
        mac_addrs=client_mac_addrs,
        client_public_address=client_public_address,
        client_public_address6=client_public_address6,
        remote_ip=remote_addr,
        connect_callback=callback,
    )

    event.wait()

    send_nonce = nacl.utils.random(nacl.public.Box.NONCE_SIZE)
    nacl_box = nacl.public.Box(priv_key, sender_pub_key)
    send_cipher_data = nacl_box.encrypt(
        json.dumps(send_data).encode(), send_nonce)
    send_cipher_data = send_cipher_data[nacl.public.Box.NONCE_SIZE:]

    send_nonce64 = base64.b64encode(send_nonce).decode()
    send_cipher_data64 = base64.b64encode(send_cipher_data).decode()

    usr.audit_event('user_profile',
        'User retrieved wg public key from pritunl client',
        remote_addr=remote_addr,
    )

    journal.entry(
        journal.USER_WG_SUCCESS,
        usr.journal_data,
        remote_address=remote_addr,
        event_long='User retrieved wg public key from pritunl client',
    )

    sync_signature = base64.b64encode(hmac.new(
        usr.sync_secret.encode(),
        (send_cipher_data64 + '&' + send_nonce64).encode(),
        hashlib.sha512).digest()).decode()

    return utils.jsonify({
        'data': send_cipher_data64,
        'nonce': send_nonce64,
        'signature': sync_signature,
    })

@app.app.route('/key/wg/<org_id>/<user_id>/<server_id>',
    methods=['PUT'])
@auth.open_auth
def key_wg_put(org_id, user_id, server_id):
    org_id = org_id
    user_id = user_id
    server_id = server_id
    remote_addr = utils.get_remote_addr()

    auth_token = flask.request.headers.get('Auth-Token', None)
    auth_timestamp = flask.request.headers.get('Auth-Timestamp', None)
    auth_nonce = flask.request.headers.get('Auth-Nonce', None)
    auth_signature = flask.request.headers.get('Auth-Signature', None)
    if not auth_token or not auth_timestamp or not auth_nonce or \
            not auth_signature:
        journal.entry(
            journal.USER_WG_FAILURE,
            remote_address=remote_addr,
            event_long='Missing auth header',
        )
        return flask.abort(406)
    auth_token = auth_token[:256]
    auth_timestamp = auth_timestamp[:64]
    auth_nonce = auth_nonce[:32]
    auth_signature = auth_signature[:512]

    try:
        if abs(int(auth_timestamp) - int(utils.time_now())) > \
                settings.app.auth_time_window:
            journal.entry(
                journal.USER_WG_FAILURE,
                remote_address=remote_addr,
                event_long='Expired auth timestamp',
            )
            return flask.abort(408)
    except ValueError:
        journal.entry(
            journal.USER_WG_FAILURE,
            remote_address=remote_addr,
            event_long='Invalid auth timestamp',
        )
        return flask.abort(405)

    org = organization.get_by_id(org_id)
    if not org:
        journal.entry(
            journal.USER_WG_FAILURE,
            remote_address=remote_addr,
            event_long='Organization not found',
        )
        return flask.abort(404)

    usr = org.get_user(id=user_id)
    if not usr:
        journal.entry(
            journal.USER_WG_FAILURE,
            remote_address=remote_addr,
            event_long='User not found',
        )
        return flask.abort(404)
    elif not usr.sync_secret:
        journal.entry(
            journal.USER_WG_FAILURE,
            usr.journal_data,
            remote_address=remote_addr,
            event_long='User missing sync secret',
        )
        return flask.abort(410)

    if auth_token != usr.sync_token:
        journal.entry(
            journal.USER_WG_FAILURE,
            usr.journal_data,
            remote_address=remote_addr,
            event_long='Sync token mismatch',
        )
        return flask.abort(411)

    if usr.disabled:
        journal.entry(
            journal.USER_WG_FAILURE,
            usr.journal_data,
            remote_address=remote_addr,
            event_long='User disabled',
        )
        return flask.abort(403)

    cipher_data64 = flask.request.json.get('data')
    box_nonce64 = flask.request.json.get('nonce')
    public_key64 = flask.request.json.get('public_key')
    signature64 = flask.request.json.get('signature')

    auth_string = '&'.join([
        usr.sync_token, auth_timestamp, auth_nonce, flask.request.method,
        flask.request.path, cipher_data64, box_nonce64, public_key64,
        signature64])

    if len(auth_string) > AUTH_SIG_STRING_MAX_LEN or len(auth_nonce) < 8:
        journal.entry(
            journal.USER_WG_FAILURE,
            usr.journal_data,
            remote_address=remote_addr,
            event_long='Invalid signature or nonce length',
        )
        return flask.abort(414)

    auth_test_signature = base64.b64encode(hmac.new(
        usr.sync_secret.encode(), auth_string.encode(),
        hashlib.sha512).digest()).decode()
    if not utils.const_compare(auth_signature, auth_test_signature):
        journal.entry(
            journal.USER_WG_FAILURE,
            usr.journal_data,
            remote_address=remote_addr,
            event_long='Auth signature mismatch',
        )
        return flask.abort(401)

    nonces_collection = mongo.get_collection('auth_nonces')
    try:
        nonces_collection.insert_one({
            'token': auth_token,
            'nonce': auth_nonce,
            'timestamp': utils.now(),
        })
    except pymongo.errors.DuplicateKeyError:
        journal.entry(
            journal.USER_WG_FAILURE,
            usr.journal_data,
            remote_address=remote_addr,
            event_long='Duplicate nonce from reconnection',
        )
        return flask.abort(409)

    svr = usr.get_server(server_id)

    sender_pub_key = nacl.public.PublicKey(
        base64.b64decode(public_key64))
    box_nonce = base64.b64decode(box_nonce64)

    priv_key = nacl.public.PrivateKey(
        base64.b64decode(svr.auth_box_private_key))

    cipher_data = base64.b64decode(cipher_data64)
    nacl_box = nacl.public.Box(priv_key, sender_pub_key)
    plaintext = nacl_box.decrypt(cipher_data, box_nonce).decode()

    try:
        nonces_collection.insert_one({
            'token': auth_token,
            'nonce': box_nonce64,
            'timestamp': utils.now(),
        })
    except pymongo.errors.DuplicateKeyError:
        journal.entry(
            journal.USER_WG_FAILURE,
            usr.journal_data,
            remote_address=remote_addr,
            event_long='Duplicate secondary nonce',
        )
        return flask.abort(412)

    key_data = json.loads(plaintext)

    client_wg_public_key = utils.filter_str(key_data['wg_public_key'])

    if len(client_wg_public_key) < 32:
        journal.entry(
            journal.USER_WG_FAILURE,
            usr.journal_data,
            remote_address=remote_addr,
            event_long='Public key too short',
        )
        return flask.abort(415)

    try:
        client_wg_public_key = base64.b64decode(client_wg_public_key)
        if len(client_wg_public_key) != 32:
            raise ValueError('Invalid length')
        client_wg_public_key = base64.b64encode(
            client_wg_public_key).decode()
    except:
        journal.entry(
            journal.USER_WG_FAILURE,
            usr.journal_data,
            remote_address=remote_addr,
            event_long='Public key invalid',
        )
        return flask.abort(416)

    wg_keys_collection = mongo.get_collection('wg_keys')
    wg_key_doc = wg_keys_collection.find_one({
        '_id': client_wg_public_key,
    })
    if not wg_key_doc:
        journal.entry(
            journal.USER_WG_FAILURE,
            usr.journal_data,
            remote_address=remote_addr,
            event_long='Public key not found',
        )
        return flask.abort(417)

    instance = server.get_instance(server_id)
    if not instance or instance.state != 'running':
        return flask.abort(429)

    if not instance.server.wg:
        return flask.abort(429)

    clients = instance.instance_com.clients

    status = clients.ping_wg(
        user=usr,
        org=org,
        wg_public_key=client_wg_public_key,
    )

    send_data = {
        'status': status,
        'timestamp': int(utils.time_now()),
    }

    send_nonce = nacl.utils.random(nacl.public.Box.NONCE_SIZE)
    nacl_box = nacl.public.Box(priv_key, sender_pub_key)
    send_cipher_data = nacl_box.encrypt(
        json.dumps(send_data).encode(), send_nonce)
    send_cipher_data = send_cipher_data[nacl.public.Box.NONCE_SIZE:]

    send_nonce64 = base64.b64encode(send_nonce).decode()
    send_cipher_data64 = base64.b64encode(send_cipher_data).decode()

    journal.entry(
        journal.USER_WG_SUCCESS,
        usr.journal_data,
        remote_address=remote_addr,
        event_long='User wg ping from pritunl client',
    )

    sync_signature = base64.b64encode(hmac.new(
        usr.sync_secret.encode(),
        (send_cipher_data64 + '&' + send_nonce64).encode(),
        hashlib.sha512).digest()).decode()

    return utils.jsonify({
        'data': send_cipher_data64,
        'nonce': send_nonce64,
        'signature': sync_signature,
    })

@app.app.route('/key/ovpn/<org_id>/<user_id>/<server_id>',
    methods=['POST'])
@auth.open_auth
def key_ovpn_post(org_id, user_id, server_id):
    org_id = org_id
    user_id = user_id
    server_id = server_id
    remote_addr = utils.get_remote_addr()

    auth_token = flask.request.headers.get('Auth-Token', None)
    auth_timestamp = flask.request.headers.get('Auth-Timestamp', None)
    auth_nonce = flask.request.headers.get('Auth-Nonce', None)
    auth_signature = flask.request.headers.get('Auth-Signature', None)
    if not auth_token or not auth_timestamp or not auth_nonce or \
            not auth_signature:
        journal.entry(
            journal.USER_OVPN_FAILURE,
            remote_address=remote_addr,
            event_long='Missing auth header',
        )
        return flask.abort(406)
    auth_token = auth_token[:256]
    auth_timestamp = auth_timestamp[:64]
    auth_nonce = auth_nonce[:32]
    auth_signature = auth_signature[:512]

    try:
        if abs(int(auth_timestamp) - int(utils.time_now())) > \
                settings.app.auth_time_window:
            journal.entry(
                journal.USER_OVPN_FAILURE,
                remote_address=remote_addr,
                event_long='Expired auth timestamp',
            )
            return flask.abort(408)
    except ValueError:
        journal.entry(
            journal.USER_OVPN_FAILURE,
            remote_address=remote_addr,
            event_long='Invalid auth timestamp',
        )
        return flask.abort(405)

    org = organization.get_by_id(org_id)
    if not org:
        journal.entry(
            journal.USER_OVPN_FAILURE,
            remote_address=remote_addr,
            event_long='Organization not found',
        )
        return flask.abort(404)

    usr = org.get_user(id=user_id)
    if not usr:
        journal.entry(
            journal.USER_OVPN_FAILURE,
            remote_address=remote_addr,
            event_long='User not found',
        )
        return flask.abort(404)
    elif not usr.sync_secret:
        journal.entry(
            journal.USER_OVPN_FAILURE,
            usr.journal_data,
            remote_address=remote_addr,
            event_long='User missing sync secret',
        )
        return flask.abort(410)

    if auth_token != usr.sync_token:
        journal.entry(
            journal.USER_OVPN_FAILURE,
            usr.journal_data,
            remote_address=remote_addr,
            event_long='Sync token mismatch',
        )
        return flask.abort(411)

    if usr.disabled:
        journal.entry(
            journal.USER_OVPN_FAILURE,
            usr.journal_data,
            remote_address=remote_addr,
            event_long='User disabled',
        )
        return flask.abort(403)

    cipher_data64 = flask.request.json.get('data')
    box_nonce64 = flask.request.json.get('nonce')
    public_key64 = flask.request.json.get('public_key')
    signature64 = flask.request.json.get('signature')
    device_signature64 = flask.request.json.get('device_signature')

    auth_string = '&'.join([
        usr.sync_token, auth_timestamp, auth_nonce, flask.request.method,
        flask.request.path, cipher_data64, box_nonce64, public_key64,
        signature64] + ([device_signature64] if device_signature64 else []))

    if len(auth_string) > AUTH_SIG_STRING_MAX_LEN:
        journal.entry(
            journal.USER_OVPN_FAILURE,
            usr.journal_data,
            remote_address=remote_addr,
            event_long='Auth string len limit exceeded',
        )
        return flask.abort(414)

    auth_test_signature = base64.b64encode(hmac.new(
        usr.sync_secret.encode(), auth_string.encode(),
        hashlib.sha512).digest()).decode()
    if not utils.const_compare(auth_signature, auth_test_signature):
        journal.entry(
            journal.USER_OVPN_FAILURE,
            usr.journal_data,
            remote_address=remote_addr,
            event_long='Auth signature mismatch',
        )
        return flask.abort(401)

    nonces_collection = mongo.get_collection('auth_nonces')
    try:
        nonces_collection.insert_one({
            'token': auth_token,
            'nonce': auth_nonce,
            'timestamp': utils.now(),
        })
    except pymongo.errors.DuplicateKeyError:
        journal.entry(
            journal.USER_OVPN_FAILURE,
            usr.journal_data,
            remote_address=remote_addr,
            event_long='Duplicate nonce from reconnection',
        )
        return flask.abort(409)

    data_hash = hashlib.sha512(
        '&'.join([cipher_data64, box_nonce64, public_key64]).encode(),
    ).digest()
    try:
        usr.verify_sig(
            data_hash,
            base64.b64decode(signature64),
        )
    except InvalidSignature:
        journal.entry(
            journal.USER_OVPN_FAILURE,
            usr.journal_data,
            remote_address=remote_addr,
            event_long='Invalid rsa signature',
        )
        return flask.abort(412)

    svr = usr.get_server(server_id)

    sender_pub_key = nacl.public.PublicKey(
        base64.b64decode(public_key64))
    box_nonce = base64.b64decode(box_nonce64)

    priv_key = nacl.public.PrivateKey(
        base64.b64decode(svr.auth_box_private_key))

    cipher_data = base64.b64decode(cipher_data64)
    nacl_box = nacl.public.Box(priv_key, sender_pub_key)
    plaintext = nacl_box.decrypt(cipher_data, box_nonce).decode()

    try:
        nonces_collection.insert_one({
            'token': auth_token,
            'nonce': box_nonce64,
            'timestamp': utils.now(),
        })
    except pymongo.errors.DuplicateKeyError:
        journal.entry(
            journal.USER_OVPN_FAILURE,
            usr.journal_data,
            remote_address=remote_addr,
            event_long='Duplicate secondary nonce',
        )
        return flask.abort(415)

    key_data = json.loads(plaintext)

    client_platform = utils.filter_str(key_data['platform'])
    client_ver = utils.filter_str(key_data.get('client_ver'))
    client_device_id = utils.filter_str(key_data['device_id'])
    client_device_name = utils.filter_str(key_data['device_name'])
    client_device_hostname = utils.filter_str(
        key_data.get('device_hostname')) or client_device_name
    client_device_key64 = utils.filter_str(key_data.get('device_key'))
    client_mac_addr = utils.filter_str(key_data['mac_addr'])
    client_mac_addrs = key_data['mac_addrs']
    if client_mac_addrs:
        client_mac_addrs = [utils.filter_str(x)
            for x in client_mac_addrs]
    else:
        client_mac_addrs = None
    client_auth_token = key_data['token']
    client_auth_nonce = utils.filter_str(key_data['nonce'])
    client_auth_password = key_data['password']
    client_auth_timestamp = int(key_data['timestamp'])
    client_public_address = utils.filter_str(key_data['public_address'])
    client_public_address6 = utils.filter_str(key_data['public_address6'])

    if client_public_address:
        client_public_address = str(ipaddress.IPv4Address(
            client_public_address))
    else:
        client_public_address = None

    if client_public_address6:
        client_public_address6 = str(ipaddress.IPv6Address(
            client_public_address6))
    else:
        client_public_address6 = None

    if ':' in remote_addr:
        remote_addr = str(ipaddress.IPv6Address(remote_addr))
    else:
        remote_addr = str(ipaddress.IPv4Address(remote_addr))

    if svr.device_auth:
        if not client_device_key64 or not device_signature64:
            journal.entry(
                journal.USER_WG_FAILURE,
                usr.journal_data,
                remote_address=remote_addr,
                event_long='Invalid device signature',
            )
            return utils.jsonify({
                'error': 'device_signature_missing',
                'error_msg': 'Device signature missing.',
            }, 400)

        try:
            usr.device_verify_sig(
                client_device_hostname,
                client_platform,
                utils.base64raw_decode(client_device_key64),
                data_hash,
                utils.base64raw_decode(device_signature64),
            )

            journal.entry(
                journal.USER_DEVICE_AUTHENTICATE_SUCCESS,
                usr.journal_data,
                device_name=client_device_hostname,
                device_platform=client_platform,
                device_public_key=client_device_key64,
                remote_address=remote_addr,
                event_long='User verified device signature',
            )
        except DeviceUnregistered as err:
            send_data = {
                'allow': False,
                'token': None,
                'reason': None,
                'reg_key': err.reg_key,
                'remote': settings.local.host.public_addr,
                'remote6': settings.local.host.public_addr6,
            }

            send_nonce = nacl.utils.random(nacl.public.Box.NONCE_SIZE)
            nacl_box = nacl.public.Box(priv_key, sender_pub_key)
            send_cipher_data = nacl_box.encrypt(
                json.dumps(send_data).encode(), send_nonce)
            send_cipher_data = send_cipher_data[nacl.public.Box.NONCE_SIZE:]

            send_nonce64 = base64.b64encode(send_nonce).decode()
            send_cipher_data64 = base64.b64encode(send_cipher_data).decode()

            usr.audit_event('user_profile',
                'User device registration required',
                remote_addr=remote_addr,
            )

            journal.entry(
                journal.USER_DEVICE_CREATE,
                usr.journal_data,
                device_name=client_device_hostname,
                device_platform=client_platform,
                device_public_key=client_device_key64,
                remote_address=remote_addr,
                event_long='Device registration required',
            )

            journal.entry(
                journal.USER_OVPN_FAILURE,
                usr.journal_data,
                remote_address=remote_addr,
                event_long='Device registration required',
            )

            sync_signature = base64.b64encode(hmac.new(
                usr.sync_secret.encode(),
                (send_cipher_data64 + '&' + send_nonce64).encode(),
                hashlib.sha512).digest()).decode()

            return utils.jsonify({
                'data': send_cipher_data64,
                'nonce': send_nonce64,
                'signature': sync_signature,
            })
        except InvalidSignature:
            journal.entry(
                journal.USER_DEVICE_AUTHENTICATE_FAILURE,
                usr.journal_data,
                device_name=client_device_hostname,
                device_platform=client_platform,
                device_public_key=client_device_key64,
                remote_address=remote_addr,
                event_long='User device signature invalid',
            )
            journal.entry(
                journal.USER_WG_FAILURE,
                usr.journal_data,
                remote_address=remote_addr,
                event_long='Invalid device signature',
            )
            return utils.jsonify({
                'error': 'device_signature_invalid',
                'error_msg': 'Device signature invalid.',
            }, 400)

    instance = server.get_instance(server_id)
    if not instance or instance.state != 'running':
        return flask.abort(429)

    if instance.server.sso_auth:
        return _key_request_init(org.id, usr.id, svr.id, 'ovpn')

    if not instance.server.dynamic_firewall and \
            not instance.server.device_auth:
        return flask.abort(431)

    clients = instance.instance_com.clients

    event = threading.Event()
    send_data = {
        'allow': None,
        'token': None,
        'reason': None,
        'remote': settings.local.host.public_addr,
        'remote6': settings.local.host.public_addr6,
    }
    def callback(allow, data):
        send_data['allow'] = allow
        if allow:
            send_data['token'] = data
        else:
            send_data['reason'] = data
        event.set()

    clients.open_ovpn(
        user=usr,
        org=org,
        auth_password=client_auth_password,
        auth_token=client_auth_token,
        auth_nonce=client_auth_nonce,
        auth_timestamp=client_auth_timestamp,
        sso_token=None,
        platform=client_platform,
        client_ver=client_ver,
        device_id=client_device_id,
        device_name=client_device_name,
        mac_addr=client_mac_addr,
        mac_addrs=client_mac_addrs,
        client_public_address=client_public_address,
        client_public_address6=client_public_address6,
        remote_ip=remote_addr,
        connect_callback=callback,
    )

    event.wait()

    send_nonce = nacl.utils.random(nacl.public.Box.NONCE_SIZE)
    nacl_box = nacl.public.Box(priv_key, sender_pub_key)
    send_cipher_data = nacl_box.encrypt(
        json.dumps(send_data).encode(), send_nonce)
    send_cipher_data = send_cipher_data[nacl.public.Box.NONCE_SIZE:]

    send_nonce64 = base64.b64encode(send_nonce).decode()
    send_cipher_data64 = base64.b64encode(send_cipher_data).decode()

    usr.audit_event('user_profile',
        'User opened ovpn connection from pritunl client',
        remote_addr=remote_addr,
    )

    journal.entry(
        journal.USER_OVPN_SUCCESS,
        usr.journal_data,
        remote_address=remote_addr,
        event_long='User opened ovpn connection from pritunl client',
    )

    sync_signature = base64.b64encode(hmac.new(
        usr.sync_secret.encode(),
        (send_cipher_data64 + '&' + send_nonce64).encode(),
        hashlib.sha512).digest()).decode()

    return utils.jsonify({
        'data': send_cipher_data64,
        'nonce': send_nonce64,
        'signature': sync_signature,
    })

def _key_request_init(org_id, user_id, server_id, mode):
    state = utils.rand_str(64)
    token = utils.rand_str(32)
    sso_mode = settings.app.sso

    if sso_mode in (RADIUS_AUTH, RADIUS_DUO_AUTH, PLUGIN_AUTH):
        logger.error(
            'Connection single sign-on not supported with current mode. ' +
              'Disable single sign-on authentication in server settings.',
            'key',
            sso_mode=sso_mode,
        )
        return flask.abort(401)

    tokens_collection = mongo.get_collection('key_tokens')
    tokens_collection.insert_one({
        '_id': state,
        'org_id': org_id,
        'user_id': user_id,
        'server_id': server_id,
        'mode': mode,
        'token': token,
        'type': KEY_REQUEST_AUTH,
        'secret': None,
        'timestamp': utils.now(),
    })

    return utils.jsonify({
        'sso_token': token,
        'sso_url': sso.server_sso_url() +
            '/key/request?state=' + state,
    })

@app.app.route('/key/request', methods=['GET'])
@auth.open_auth
def key_request_get():
    sso_mode = settings.app.sso

    if sso_mode not in (AZURE_AUTH, AZURE_DUO_AUTH, AZURE_YUBICO_AUTH,
            GOOGLE_AUTH, GOOGLE_DUO_AUTH, GOOGLE_YUBICO_AUTH,
            AUTHZERO_AUTH, AUTHZERO_DUO_AUTH, AUTHZERO_YUBICO_AUTH,
            SLACK_AUTH, SLACK_DUO_AUTH, SLACK_YUBICO_AUTH, SAML_AUTH,
            SAML_DUO_AUTH, SAML_YUBICO_AUTH, SAML_OKTA_AUTH,
            SAML_OKTA_DUO_AUTH, SAML_OKTA_YUBICO_AUTH, SAML_ONELOGIN_AUTH,
            SAML_ONELOGIN_DUO_AUTH, SAML_ONELOGIN_YUBICO_AUTH,
            SAML_JUMPCLOUD_AUTH, SAML_JUMPCLOUD_DUO_AUTH,
            SAML_JUMPCLOUD_YUBICO_AUTH):
        return flask.abort(404)

    state = flask.request.args.get('state')

    tokens_collection = mongo.get_collection('key_tokens')
    doc = tokens_collection.find_one_and_delete({
        '_id': state,
    })

    if not doc or doc['type'] != KEY_REQUEST_AUTH:
        return flask.abort(404)

    org_id = doc['org_id']
    user_id = doc['user_id']
    server_id = doc['server_id']
    token = doc['token']
    mode = doc['mode']

    state = utils.rand_str(64)
    secret = utils.rand_str(64)
    callback = utils.get_url_root() + '/key/callback'
    auth_server = AUTH_SERVER
    if settings.app.dedicated:
        auth_server = settings.app.dedicated

    if not settings.local.sub_active:
        logger.error('Subscription must be active for sso', 'sso')
        return flask.abort(405)

    if AZURE_AUTH in sso_mode:
        resp = requests.post(auth_server + '/v1/request/azure',
            headers={
                'Content-Type': 'application/json',
            },
            json={
                'license': settings.app.license,
                'callback': callback,
                'state': state,
                'secret': secret,
                'region': settings.app.sso_azure_region or '',
                'directory_id': settings.app.sso_azure_directory_id,
                'app_id': settings.app.sso_azure_app_id,
                'app_secret': settings.app.sso_azure_app_secret,
            },
        )

        if resp.status_code != 200:
            logger.error('Azure auth server error', 'sso',
                status_code=resp.status_code,
                content=resp.content,
            )

            if resp.status_code == 401:
                return flask.abort(405)

            return flask.abort(500)

        tokens_collection = mongo.get_collection('key_tokens')
        tokens_collection.insert_one({
            '_id': state,
            'org_id': org_id,
            'user_id': user_id,
            'server_id': server_id,
            'mode': mode,
            'token': token,
            'type': AZURE_AUTH,
            'secret': secret,
            'timestamp': utils.now(),
        })

        data = resp.json()

        return utils.redirect(data['url'])

    elif GOOGLE_AUTH in sso_mode:
        resp = requests.post(auth_server + '/v1/request/google',
            headers={
                'Content-Type': 'application/json',
            },
            json={
                'license': settings.app.license,
                'callback': callback,
                'state': state,
                'secret': secret,
            },
        )

        if resp.status_code != 200:
            logger.error('Google auth server error', 'sso',
                status_code=resp.status_code,
                content=resp.content,
            )

            if resp.status_code == 401:
                return flask.abort(405)

            return flask.abort(500)

        tokens_collection = mongo.get_collection('key_tokens')
        tokens_collection.insert_one({
            '_id': state,
            'org_id': org_id,
            'user_id': user_id,
            'server_id': server_id,
            'mode': mode,
            'token': token,
            'type': GOOGLE_AUTH,
            'secret': secret,
            'timestamp': utils.now(),
        })

        data = resp.json()

        return utils.redirect(data['url'])

    elif AUTHZERO_AUTH in sso_mode:
        resp = requests.post(auth_server + '/v1/request/authzero',
            headers={
                'Content-Type': 'application/json',
            },
            json={
                'license': settings.app.license,
                'callback': callback,
                'state': state,
                'secret': secret,
                'app_domain': settings.app.sso_authzero_domain,
                'app_id': settings.app.sso_authzero_app_id,
                'app_secret': settings.app.sso_authzero_app_secret,
            },
                             )

        if resp.status_code != 200:
            logger.error('Auth0 auth server error', 'sso',
                status_code=resp.status_code,
                content=resp.content,
            )

            if resp.status_code == 401:
                return flask.abort(405)

            return flask.abort(500)

        tokens_collection = mongo.get_collection('key_tokens')
        tokens_collection.insert_one({
            '_id': state,
            'org_id': org_id,
            'user_id': user_id,
            'server_id': server_id,
            'mode': mode,
            'token': token,
            'type': AUTHZERO_AUTH,
            'secret': secret,
            'timestamp': utils.now(),
        })

        data = resp.json()

        return utils.redirect(data['url'])

    elif SLACK_AUTH in sso_mode:
        resp = requests.post(auth_server + '/v1/request/slack',
            headers={
                'Content-Type': 'application/json',
            },
            json={
                'license': settings.app.license,
                'callback': callback,
                'state': state,
                'secret': secret,
            },
                             )

        if resp.status_code != 200:
            logger.error('Slack auth server error', 'sso',
                status_code=resp.status_code,
                content=resp.content,
            )

            if resp.status_code == 401:
                return flask.abort(405)

            return flask.abort(500)

        tokens_collection = mongo.get_collection('key_tokens')
        tokens_collection.insert_one({
            '_id': state,
            'org_id': org_id,
            'user_id': user_id,
            'server_id': server_id,
            'mode': mode,
            'token': token,
            'type': SLACK_AUTH,
            'secret': secret,
            'timestamp': utils.now(),
        })

        data = resp.json()

        return utils.redirect(data['url'])

    elif SAML_AUTH in sso_mode:
        resp = requests.post(auth_server + '/v1/request/saml',
            headers={
                'Content-Type': 'application/json',
            },
            json={
                'license': settings.app.license,
                'callback': callback,
                'state': state,
                'secret': secret,
                'sso_url': settings.app.sso_saml_url,
                'issuer_url': settings.app.sso_saml_issuer_url,
                'cert': settings.app.sso_saml_cert,
            },
        )

        if resp.status_code != 200:
            logger.error('Saml auth server error', 'sso',
                status_code=resp.status_code,
                content=resp.content,
            )

            if resp.status_code == 401:
                return flask.abort(405)

            return flask.abort(500)

        tokens_collection = mongo.get_collection('key_tokens')
        tokens_collection.insert_one({
            '_id': state,
            'org_id': org_id,
            'user_id': user_id,
            'server_id': server_id,
            'mode': mode,
            'token': token,
            'type': SAML_AUTH,
            'secret': secret,
            'timestamp': utils.now(),
        })

        return flask.Response(
            status=200,
            response=resp.content,
            content_type="text/html;charset=utf-8",
        )
    else:
        return flask.abort(404)

def _key_sso_validate(key_doc, username, email, sso_mode, org_id, groups,
    remote_addr, http_redirect=False, yubico_id=None):

    org = organization.get_by_id(key_doc['org_id'])
    if not org:
        journal.entry(
            journal.USER_OVPN_FAILURE,
            remote_address=remote_addr,
            event_long='Organization not found',
        )
        return flask.abort(404)

    usr = org.get_user(id=key_doc['user_id'])
    if not usr:
        journal.entry(
            journal.USER_OVPN_FAILURE,
            remote_address=remote_addr,
            event_long='User not found',
        )
        return flask.abort(404)

    if usr.name != username:
        logger.warning('Username changed, must reimport profile', 'sso',
            auth_username=usr.name,
            sso_username=username,
        )
        journal.entry(
            journal.USER_CONNECT_SSO_FAILURE,
            auth_username=usr.name,
            sso_username=username,
            remote_address=remote_addr,
            event_long='Username mismatch',
        )
        return utils.jsonify({
            'error': SSO_USERNAME_MISMATCH,
            'error_msg': SSO_USERNAME_MISMATCH_MSG,
        }, 401)

    if org.id != org_id:
        logger.warning('Organization changed, must reimport profile', 'sso',
            auth_org_id=org.id,
            sso_org_id=org_id,
        )
        journal.entry(
            journal.USER_CONNECT_SSO_FAILURE,
            auth_org_id=org.id,
            sso_org_id=org_id,
            remote_address=remote_addr,
            event_long='Organization mismatch',
        )
        return utils.jsonify({
            'error': SSO_ORGANIZATION_MISMATCH,
            'error_msg': SSO_ORGANIZATION_MISMATCH_MSG,
        }, 401)

    if yubico_id and usr.yubico_id and yubico_id != usr.yubico_id:
        journal.entry(
            journal.SSO_AUTH_FAILURE,
            user_name=username,
            remote_address=remote_addr,
            reason=journal.SSO_AUTH_REASON_INVALID_YUBIKEY,
            reason_long='Invalid yubikey id',
        )

        return utils.jsonify({
            'error': YUBIKEY_INVALID,
            'error_msg': YUBIKEY_INVALID_MSG,
        }, 401)

    if usr.disabled:
        return flask.abort(403)

    changed = False

    if yubico_id and not usr.yubico_id:
        changed = True
        usr.yubico_id = yubico_id
        usr.commit('yubico_id')

    if groups and groups != set(usr.groups or []):
        changed = True
        usr.groups = list(groups)
        usr.commit('groups')

    if usr.auth_type != sso_mode:
        changed = True
        usr.auth_type = sso_mode
        usr.commit('auth_type')

    if changed:
        event.Event(type=USERS_UPDATED, resource_id=org.id)

    key_link = org.create_user_key_link(usr.id, one_time=True)

    usr.audit_event('user_profile',
        'User profile viewed from single sign-on',
        remote_addr=remote_addr,
    )

    journal.entry(
        journal.SSO_AUTH_SUCCESS,
        usr.journal_data,
        key_id_hash=utils.unsafe_md5(key_link['id'].encode()).hexdigest(),
        remote_address=remote_addr,
    )

    journal.entry(
        journal.USER_PROFILE_SUCCESS,
        usr.journal_data,
        remote_address=remote_addr,
        event_long='User profile viewed from single sign-on',
    )

    messenger.publish('tokens', 'authorized', extra={
        'user_id': usr.id,
        'server_id': key_doc['server_id'],
        'token': key_doc['token'],
    })

    tokens_collection = mongo.get_collection('server_sso_tokens')
    tokens_collection.insert_one({
        '_id': key_doc['token'],
        'user_id': usr.id,
        'server_id': key_doc['server_id'],
        'stage': 'open',
        'timestamp': utils.now(),
    })

    if http_redirect:
        return utils.redirect(utils.get_url_root() + "/success")
    else:
        return utils.jsonify({
            'redirect': utils.get_url_root() + "/success",
        }, 200)

@app.app.route('/key/callback', methods=['GET'])
@auth.open_auth
def key_callback_get():
    sso_mode = settings.app.sso

    if sso_mode not in (AZURE_AUTH, AZURE_DUO_AUTH, AZURE_YUBICO_AUTH,
            GOOGLE_AUTH, GOOGLE_DUO_AUTH, GOOGLE_YUBICO_AUTH,
            AUTHZERO_AUTH, AUTHZERO_DUO_AUTH, AUTHZERO_YUBICO_AUTH,
            SLACK_AUTH, SLACK_DUO_AUTH, SLACK_YUBICO_AUTH, SAML_AUTH,
            SAML_DUO_AUTH, SAML_YUBICO_AUTH, SAML_OKTA_AUTH,
            SAML_OKTA_DUO_AUTH, SAML_OKTA_YUBICO_AUTH, SAML_ONELOGIN_AUTH,
            SAML_ONELOGIN_DUO_AUTH, SAML_ONELOGIN_YUBICO_AUTH,
            SAML_JUMPCLOUD_AUTH, SAML_JUMPCLOUD_DUO_AUTH,
            SAML_JUMPCLOUD_YUBICO_AUTH):
        return flask.abort(405)

    remote_addr = utils.get_remote_addr()
    state = flask.request.args.get('state')
    sig = flask.request.args.get('sig')

    tokens_collection = mongo.get_collection('key_tokens')
    doc = tokens_collection.find_one_and_delete({
        '_id': state,
    })

    if not doc:
        return flask.abort(404)

    org_id = doc['org_id']
    user_id = doc['user_id']
    server_id = doc['server_id']

    org = organization.get_by_id(org_id)
    usr = org.get_user(user_id)
    if usr.disabled:
        return flask.abort(403)

    query = flask.request.query_string.split('&sig='.encode())[0]
    test_sig = base64.urlsafe_b64encode(hmac.new(str(doc['secret']).encode(),
        query, hashlib.sha512).digest()).decode()
    if not utils.const_compare(sig, test_sig):
        journal.entry(
            journal.SSO_AUTH_FAILURE,
            state=state,
            remote_address=remote_addr,
            reason=journal.SSO_AUTH_REASON_INVALID_CALLBACK,
            reason_long='Signature mismatch',
        )
        return flask.abort(401)

    params = urllib.parse.parse_qs(query.decode())

    if doc.get('type') == SAML_AUTH:
        username = params.get('username')[0]
        email = params.get('email', [None])[0]

        org_names = []
        if params.get('org'):
            org_names_param = params.get('org')[0]
            if ';' in org_names_param:
                org_names = org_names_param.split(';')
            else:
                org_names = org_names_param.split(',')
            org_names = [utils.filter_unicode(x) for x in org_names if x]
        org_names = sorted(org_names)

        groups = []
        if params.get('groups'):
            groups_param = params.get('groups')[0]
            if ';' in groups_param:
                groups = groups_param.split(';')
            else:
                groups = groups_param.split(',')
            groups = [utils.filter_unicode(x) for x in groups if x]
        groups = set(groups)

        if not username:
            return flask.abort(406)

        org_id = settings.app.sso_org
        if org_names:
            not_found = False
            for org_name in org_names:
                org = organization.get_by_name(
                    org_name,
                    fields=('_id'),
                )
                if org:
                    not_found = False
                    org_id = org.id
                    break
                else:
                    not_found = True

            if not_found:
                logger.warning('Supplied org names do not exists',
                    'sso',
                    sso_type=doc.get('type'),
                    user_name=username,
                    user_email=email,
                    org_names=org_names,
                )

        valid, org_id_new, groups2 = sso.plugin_sso_authenticate(
            sso_type='saml',
            user_name=username,
            user_email=email,
            remote_ip=remote_addr,
            sso_org_names=org_names,
            sso_group_names=groups,
        )
        if valid:
            org_id = org_id_new or org_id
        else:
            logger.error('Saml plugin authentication not valid', 'sso',
                username=username,
            )

            journal.entry(
                journal.SSO_AUTH_FAILURE,
                user_name=username,
                remote_address=remote_addr,
                reason=journal.SSO_AUTH_REASON_PLUGIN_FAILED,
                reason_long='Saml plugin authentication failed',
            )

            return flask.abort(401)

        groups = groups | set(groups2 or [])
    elif doc.get('type') == SLACK_AUTH:
        username = params.get('username')[0]
        email = None
        user_team = params.get('team')[0]
        org_names = params.get('orgs', [''])[0]
        org_names = sorted(org_names.split(','))
        org_names = [utils.filter_unicode(x) for x in org_names]

        if user_team != settings.app.sso_match[0]:
            journal.entry(
                journal.SSO_AUTH_FAILURE,
                user_name=username,
                remote_address=remote_addr,
                reason=journal.SSO_AUTH_REASON_SLACK_FAILED,
                reason_long='Slack team not valid',
            )

            return flask.abort(401)

        not_found = False
        org_id = settings.app.sso_org
        for org_name in org_names:
            org = organization.get_by_name(
                org_name,
                fields=('_id'),
            )
            if org:
                not_found = False
                org_id = org.id
                break
            else:
                not_found = True

        if not_found:
            logger.warning('Supplied org names do not exists',
                'sso',
                sso_type=doc.get('type'),
                user_name=username,
                user_email=email,
                org_names=org_names,
            )

        valid, org_id_new, groups = sso.plugin_sso_authenticate(
            sso_type='slack',
            user_name=username,
            user_email=email,
            remote_ip=remote_addr,
            sso_org_names=org_names,
        )
        if valid:
            org_id = org_id_new or org_id
        else:
            logger.error('Slack plugin authentication not valid', 'sso',
                username=username,
            )

            journal.entry(
                journal.SSO_AUTH_FAILURE,
                user_name=username,
                remote_address=remote_addr,
                reason=journal.SSO_AUTH_REASON_PLUGIN_FAILED,
                reason_long='Slack plugin authentication failed',
            )

            return flask.abort(401)
        groups = set(groups or [])
    elif doc.get('type') == GOOGLE_AUTH:
        username = params.get('username')[0]
        email = username

        valid, google_groups = sso.verify_google(username)
        if not valid:
            journal.entry(
                journal.SSO_AUTH_FAILURE,
                user_name=username,
                remote_address=remote_addr,
                reason=journal.SSO_AUTH_REASON_GOOGLE_FAILED,
                reason_long='Google authentication failed',
            )

            return flask.abort(401)

        org_id = settings.app.sso_org

        valid, org_id_new, groups = sso.plugin_sso_authenticate(
            sso_type='google',
            user_name=username,
            user_email=email,
            remote_ip=remote_addr,
            sso_group_names=google_groups,
        )
        if valid:
            org_id = org_id_new or org_id
        else:
            logger.error('Google plugin authentication not valid', 'sso',
                username=username,
            )

            journal.entry(
                journal.SSO_AUTH_FAILURE,
                user_name=username,
                remote_address=remote_addr,
                reason=journal.SSO_AUTH_REASON_PLUGIN_FAILED,
                reason_long='Google plugin authentication failed',
            )

            return flask.abort(401)
        groups = set(groups or [])

        if settings.app.sso_google_mode == 'groups':
            groups = groups | set(google_groups)
        else:
            not_found = False
            google_groups = sorted(google_groups)
            for org_name in google_groups:
                org = organization.get_by_name(
                    org_name,
                    fields=('_id'),
                )
                if org:
                    not_found = False
                    org_id = org.id
                    break
                else:
                    not_found = True

            if not_found:
                logger.warning('Supplied org names do not exists',
                    'sso',
                    sso_type=doc.get('type'),
                    user_name=username,
                    user_email=email,
                    org_names=google_groups,
                )
    elif doc.get('type') == AZURE_AUTH:
        username = params.get('username')[0]
        email = None

        tenant, username = username.split('/', 2)
        if tenant != settings.app.sso_azure_directory_id:
            logger.error('Azure directory ID mismatch', 'sso',
                username=username,
            )

            journal.entry(
                journal.SSO_AUTH_FAILURE,
                user_name=username,
                azure_tenant=tenant,
                remote_address=remote_addr,
                reason=journal.SSO_AUTH_REASON_AZURE_FAILED,
                reason_long='Azure directory ID mismatch',
            )

            return flask.abort(401)

        valid, azure_groups = sso.verify_azure(username)
        if not valid:
            journal.entry(
                journal.SSO_AUTH_FAILURE,
                user_name=username,
                remote_address=remote_addr,
                reason=journal.SSO_AUTH_REASON_AZURE_FAILED,
                reason_long='Azure authentication failed',
            )

            return flask.abort(401)

        org_id = settings.app.sso_org

        valid, org_id_new, groups = sso.plugin_sso_authenticate(
            sso_type='azure',
            user_name=username,
            user_email=email,
            remote_ip=remote_addr,
            sso_group_names=azure_groups,
        )
        if valid:
            org_id = org_id_new or org_id
        else:
            logger.error('Azure plugin authentication not valid', 'sso',
                username=username,
            )

            journal.entry(
                journal.SSO_AUTH_FAILURE,
                user_name=username,
                remote_address=remote_addr,
                reason=journal.SSO_AUTH_REASON_PLUGIN_FAILED,
                reason_long='Azure plugin authentication failed',
            )

            return flask.abort(401)
        groups = set(groups or [])

        if settings.app.sso_azure_mode == 'groups':
            groups = groups | set(azure_groups)
        else:
            not_found = False
            azure_groups = sorted(azure_groups)
            for org_name in azure_groups:
                org = organization.get_by_name(
                    org_name,
                    fields=('_id'),
                )
                if org:
                    not_found = False
                    org_id = org.id
                    break
                else:
                    not_found = True

            if not_found:
                logger.warning('Supplied org names do not exists',
                    'sso',
                    sso_type=doc.get('type'),
                    user_name=username,
                    user_email=email,
                    org_names=azure_groups,
                )
    elif doc.get('type') == AUTHZERO_AUTH:
        username = params.get('username')[0]
        if params.get('email'):
            email = params.get('email')[0]
        else:
            email = None

        valid, authzero_groups = sso.verify_authzero(username)
        if not valid:
            journal.entry(
                journal.SSO_AUTH_FAILURE,
                user_name=username,
                remote_address=remote_addr,
                reason=journal.SSO_AUTH_REASON_AUTHZERO_FAILED,
                reason_long='Auth0 authentication failed',
            )

            return flask.abort(401)

        org_id = settings.app.sso_org

        valid, org_id_new, groups = sso.plugin_sso_authenticate(
            sso_type='authzero',
            user_name=username,
            user_email=email,
            remote_ip=remote_addr,
        )
        if valid:
            org_id = org_id_new or org_id
        else:
            logger.error('Auth0 plugin authentication not valid', 'sso',
                username=username,
            )

            journal.entry(
                journal.SSO_AUTH_FAILURE,
                user_name=username,
                remote_address=remote_addr,
                reason=journal.SSO_AUTH_REASON_PLUGIN_FAILED,
                reason_long='Auth0 plugin authentication failed',
            )

            return flask.abort(401)
        groups = set(groups or [])

        if settings.app.sso_authzero_mode == 'groups':
            groups = groups | set(authzero_groups)
        else:
            not_found = False
            authzero_groups = sorted(authzero_groups)
            for org_name in authzero_groups:
                org = organization.get_by_name(
                    org_name,
                    fields=('_id'),
                )
                if org:
                    not_found = False
                    org_id = org.id
                    break
                else:
                    not_found = True

            if not_found:
                logger.warning('Supplied org names do not exists',
                    'sso',
                    sso_type=doc.get('type'),
                    user_name=username,
                    user_email=email,
                    org_names=authzero_groups,
                )
    else:
        logger.error('Unknown sso type', 'sso',
            sso_type=doc.get('type'),
        )
        return flask.abort(401)

    if DUO_AUTH in sso_mode:
        state = utils.generate_secret()

        tokens_collection = mongo.get_collection('key_tokens')
        tokens_collection.insert_one({
            '_id': state,
            'org_id': doc['org_id'],
            'user_id': doc['user_id'],
            'server_id': doc['server_id'],
            'mode': doc['mode'],
            'token': doc['token'],
            'type': DUO_AUTH,
            'username': username,
            'email': email,
            'groups': list(groups) if groups else None,
            'timestamp': utils.now(),
        })

        duo_page = static.StaticFile(settings.conf.www_path,
            'duo.html', cache=False, gzip=False)

        sso_duo_mode = settings.app.sso_duo_mode
        if sso_duo_mode == 'passcode':
            duo_mode = 'passcode'
        elif sso_duo_mode == 'phone':
            duo_mode = 'phone'
        else:
            duo_mode = 'push'

        body_class = duo_mode
        if settings.app.theme == 'dark':
            body_class += ' dark'

        duo_page.data = duo_page.data.replace('<%= body_class %>',
            body_class)
        duo_page.data = duo_page.data.replace('<%= token %>', state)
        duo_page.data = duo_page.data.replace('<%= duo_mode %>', duo_mode)
        duo_page.data = duo_page.data.replace(
            '<%= post_path %>', '/key/duo')

        return duo_page.get_response()

    if usr.yubico_id or YUBICO_AUTH in sso_mode:
        state = utils.generate_secret()

        tokens_collection = mongo.get_collection('key_tokens')
        tokens_collection.insert_one({
            '_id': state,
            'org_id': doc['org_id'],
            'user_id': doc['user_id'],
            'server_id': doc['server_id'],
            'mode': doc['mode'],
            'token': doc['token'],
            'type': YUBICO_AUTH,
            'username': username,
            'email': email,
            'groups': list(groups) if groups else None,
            'timestamp': utils.now(),
        })

        yubico_page = static.StaticFile(settings.conf.www_path,
            'yubico.html', cache=False, gzip=False)

        if settings.app.theme == 'dark':
            yubico_page.data = yubico_page.data.replace(
                '<body>', '<body class="dark">')
        yubico_page.data = yubico_page.data.replace('<%= token %>', state)
        yubico_page.data = yubico_page.data.replace(
            '<%= post_path %>', '/key/yubico')

        return yubico_page.get_response()

    return _key_sso_validate(doc, username, email, sso_mode, org_id,
        groups, remote_addr, http_redirect=True)

@app.app.route('/key/duo', methods=['POST'])
@auth.open_auth
def key_duo_post():
    remote_addr = utils.get_remote_addr()
    sso_mode = settings.app.sso
    token = utils.filter_str(flask.request.json.get('token')) or None
    passcode = utils.filter_str(flask.request.json.get('passcode')) or ''

    if sso_mode not in (DUO_AUTH, AZURE_DUO_AUTH, GOOGLE_DUO_AUTH,
            SLACK_DUO_AUTH, SAML_DUO_AUTH, SAML_OKTA_DUO_AUTH,
            SAML_ONELOGIN_DUO_AUTH, SAML_JUMPCLOUD_DUO_AUTH,
            RADIUS_DUO_AUTH):
        return flask.abort(404)

    if not token:
        return utils.jsonify({
            'error': TOKEN_INVALID,
            'error_msg': TOKEN_INVALID_MSG,
        }, 401)

    tokens_collection = mongo.get_collection('key_tokens')
    doc = tokens_collection.find_one_and_delete({
        '_id': token,
    })
    if not doc or doc['_id'] != token or doc['type'] != DUO_AUTH:
        journal.entry(
            journal.SSO_AUTH_FAILURE,
            remote_address=remote_addr,
            reason=journal.SSO_AUTH_REASON_INVALID_TOKEN,
            reason_long='Invalid Duo authentication token',
        )

        return utils.jsonify({
            'error': TOKEN_INVALID,
            'error_msg': TOKEN_INVALID_MSG,
        }, 401)

    username = doc['username']
    email = doc['email']
    org_id = doc['org_id']
    groups = set(doc['groups'] or [])

    if settings.app.sso_duo_mode == 'passcode':
        duo_auth = sso.Duo(
            username=username,
            factor=settings.app.sso_duo_mode,
            remote_ip=remote_addr,
            auth_type='Key',
            passcode=passcode,
        )
        valid = duo_auth.authenticate()
        if not valid:
            logger.warning('Duo authentication not valid', 'sso',
                username=username,
            )

            journal.entry(
                journal.SSO_AUTH_FAILURE,
                username=username,
                remote_address=remote_addr,
                reason=journal.SSO_AUTH_REASON_DUO_FAILED,
                reason_long='Duo passcode authentication failed',
            )

            return utils.jsonify({
                'error': PASSCODE_INVALID,
                'error_msg': PASSCODE_INVALID_MSG,
            }, 401)
    else:
        duo_auth = sso.Duo(
            username=username,
            factor=settings.app.sso_duo_mode,
            remote_ip=remote_addr,
            auth_type='Key',
        )
        valid = duo_auth.authenticate()
        if not valid:
            logger.warning('Duo authentication not valid', 'sso',
                username=username,
            )

            journal.entry(
                journal.SSO_AUTH_FAILURE,
                remote_address=remote_addr,
                reason=journal.SSO_AUTH_REASON_DUO_FAILED,
                reason_long='Duo authentication failed',
            )

            return utils.jsonify({
                'error': DUO_FAILED,
                'error_msg': DUO_FAILED_MSG,
            }, 401)

    valid, org_id_new, groups2 = sso.plugin_sso_authenticate(
        sso_type='duo',
        user_name=username,
        user_email=email,
        remote_ip=remote_addr,
    )
    if valid:
        org_id = org_id_new or org_id
    else:
        logger.warning('Duo plugin authentication not valid', 'sso',
            username=username,
        )

        journal.entry(
            journal.SSO_AUTH_FAILURE,
            user_name=username,
            remote_address=remote_addr,
            reason=journal.SSO_AUTH_REASON_PLUGIN_FAILED,
            reason_long='Duo plugin authentication failed',
        )

        return flask.abort(401)

    groups = groups | set(groups2 or [])

    return _key_sso_validate(doc, username, email, sso_mode, org_id,
        groups, remote_addr)

@app.app.route('/key/yubico', methods=['POST'])
@auth.open_auth
def key_yubico_post():
    remote_addr = utils.get_remote_addr()
    sso_mode = settings.app.sso
    token = utils.filter_str(flask.request.json.get('token')) or None
    key = utils.filter_str(flask.request.json.get('key')) or None

    if sso_mode not in (AZURE_AUTH, AZURE_DUO_AUTH, AZURE_YUBICO_AUTH,
            GOOGLE_AUTH, GOOGLE_DUO_AUTH, GOOGLE_YUBICO_AUTH,
            AUTHZERO_AUTH, AUTHZERO_DUO_AUTH, AUTHZERO_YUBICO_AUTH,
            SLACK_AUTH, SLACK_DUO_AUTH, SLACK_YUBICO_AUTH, SAML_AUTH,
            SAML_DUO_AUTH, SAML_YUBICO_AUTH, SAML_OKTA_AUTH,
            SAML_OKTA_DUO_AUTH, SAML_OKTA_YUBICO_AUTH, SAML_ONELOGIN_AUTH,
            SAML_ONELOGIN_DUO_AUTH, SAML_ONELOGIN_YUBICO_AUTH,
            SAML_JUMPCLOUD_AUTH, SAML_JUMPCLOUD_DUO_AUTH,
            SAML_JUMPCLOUD_YUBICO_AUTH):
        return flask.abort(404)

    if not token or not key:
        return utils.jsonify({
            'error': TOKEN_INVALID,
            'error_msg': TOKEN_INVALID_MSG,
        }, 401)

    tokens_collection = mongo.get_collection('key_tokens')
    doc = tokens_collection.find_one_and_delete({
        '_id': token,
    })
    if not doc or doc['_id'] != token or doc['type'] != YUBICO_AUTH:
        journal.entry(
            journal.SSO_AUTH_FAILURE,
            remote_address=remote_addr,
            reason=journal.SSO_AUTH_REASON_INVALID_TOKEN,
            reason_long='Invalid Yubikey authentication token',
        )

        return utils.jsonify({
            'error': TOKEN_INVALID,
            'error_msg': TOKEN_INVALID_MSG,
        }, 401)

    username = doc['username']
    email = doc['email']
    org_id = doc['org_id']
    groups = set(doc['groups'] or [])

    valid, yubico_id = sso.auth_yubico(key)
    if not valid or not yubico_id:
        journal.entry(
            journal.SSO_AUTH_FAILURE,
            username=username,
            remote_address=remote_addr,
            reason=journal.SSO_AUTH_REASON_YUBIKEY_FAILED,
            reason_long='Yubikey authentication failed',
        )

        return utils.jsonify({
            'error': YUBIKEY_INVALID,
            'error_msg': YUBIKEY_INVALID_MSG,
        }, 401)

    return _key_sso_validate(doc, username, email, sso_mode, org_id,
        groups, remote_addr, yubico_id=yubico_id)

@app.app.route('/key/ovpn_wait/<org_id>/<user_id>/<server_id>',
    methods=['POST'])
@auth.open_auth
def key_ovpn_wait_post(org_id, user_id, server_id):
    org_id = org_id
    user_id = user_id
    server_id = server_id
    remote_addr = utils.get_remote_addr()

    auth_token = flask.request.headers.get('Auth-Token', None)
    auth_timestamp = flask.request.headers.get('Auth-Timestamp', None)
    auth_nonce = flask.request.headers.get('Auth-Nonce', None)
    auth_signature = flask.request.headers.get('Auth-Signature', None)
    if not auth_token or not auth_timestamp or not auth_nonce or \
            not auth_signature:
        journal.entry(
            journal.USER_KEY_FAILURE,
            remote_address=remote_addr,
            event_long='Missing auth header',
        )
        return flask.abort(406)
    auth_token = auth_token[:256]
    auth_timestamp = auth_timestamp[:64]
    auth_nonce = auth_nonce[:32]
    auth_signature = auth_signature[:512]

    try:
        if abs(int(auth_timestamp) - int(utils.time_now())) > \
                settings.app.auth_time_window:
            journal.entry(
                journal.USER_KEY_FAILURE,
                remote_address=remote_addr,
                event_long='Expired auth timestamp',
            )
            return flask.abort(408)
    except ValueError:
        journal.entry(
            journal.USER_KEY_FAILURE,
            remote_address=remote_addr,
            event_long='Invalid auth timestamp',
        )
        return flask.abort(405)

    org = organization.get_by_id(org_id)
    if not org:
        journal.entry(
            journal.USER_KEY_FAILURE,
            remote_address=remote_addr,
            event_long='Organization not found',
        )
        return flask.abort(404)

    usr = org.get_user(id=user_id)
    if not usr:
        journal.entry(
            journal.USER_KEY_FAILURE,
            remote_address=remote_addr,
            event_long='User not found',
        )
        return flask.abort(404)
    elif not usr.sync_secret:
        journal.entry(
            journal.USER_KEY_FAILURE,
            usr.journal_data,
            remote_address=remote_addr,
            event_long='User missing sync secret',
        )
        return flask.abort(410)

    if auth_token != usr.sync_token:
        journal.entry(
            journal.USER_KEY_FAILURE,
            usr.journal_data,
            remote_address=remote_addr,
            event_long='Sync token mismatch',
        )
        return flask.abort(411)

    if usr.disabled:
        journal.entry(
            journal.USER_KEY_FAILURE,
            usr.journal_data,
            remote_address=remote_addr,
            event_long='User disabled',
        )
        return flask.abort(403)

    cipher_data64 = flask.request.json.get('data')
    box_nonce64 = flask.request.json.get('nonce')
    public_key64 = flask.request.json.get('public_key')
    signature64 = flask.request.json.get('signature')
    device_signature64 = flask.request.json.get('device_signature')

    auth_string = '&'.join([
        usr.sync_token, auth_timestamp, auth_nonce, flask.request.method,
        flask.request.path, cipher_data64, box_nonce64, public_key64,
        signature64] + ([device_signature64] if device_signature64 else []))

    if len(auth_string) > AUTH_SIG_STRING_MAX_LEN:
        journal.entry(
            journal.USER_KEY_FAILURE,
            usr.journal_data,
            remote_address=remote_addr,
            event_long='Auth string len limit exceeded',
        )
        return flask.abort(414)

    auth_test_signature = base64.b64encode(hmac.new(
        usr.sync_secret.encode(), auth_string.encode(),
        hashlib.sha512).digest()).decode()
    if not utils.const_compare(auth_signature, auth_test_signature):
        journal.entry(
            journal.USER_KEY_FAILURE,
            usr.journal_data,
            remote_address=remote_addr,
            event_long='Auth signature mismatch',
        )
        return flask.abort(401)

    nonces_collection = mongo.get_collection('auth_nonces')
    try:
        nonces_collection.insert_one({
            'token': auth_token,
            'nonce': auth_nonce,
            'timestamp': utils.now(),
        })
    except pymongo.errors.DuplicateKeyError:
        journal.entry(
            journal.USER_KEY_FAILURE,
            usr.journal_data,
            remote_address=remote_addr,
            event_long='Duplicate nonce from reconnection',
        )
        return flask.abort(409)

    data_hash = hashlib.sha512(
        '&'.join([cipher_data64, box_nonce64, public_key64]).encode(),
    ).digest()
    try:
        usr.verify_sig(
            data_hash,
            base64.b64decode(signature64),
        )
    except InvalidSignature:
        journal.entry(
            journal.USER_KEY_FAILURE,
            usr.journal_data,
            remote_address=remote_addr,
            event_long='Invalid rsa signature',
        )
        return flask.abort(412)

    svr = usr.get_server(server_id)

    sender_pub_key = nacl.public.PublicKey(
        base64.b64decode(public_key64))
    box_nonce = base64.b64decode(box_nonce64)

    priv_key = nacl.public.PrivateKey(
        base64.b64decode(svr.auth_box_private_key))

    cipher_data = base64.b64decode(cipher_data64)
    nacl_box = nacl.public.Box(priv_key, sender_pub_key)
    plaintext = nacl_box.decrypt(cipher_data, box_nonce).decode()

    try:
        nonces_collection.insert_one({
            'token': auth_token,
            'nonce': box_nonce64,
            'timestamp': utils.now(),
        })
    except pymongo.errors.DuplicateKeyError:
        journal.entry(
            journal.USER_KEY_FAILURE,
            usr.journal_data,
            remote_address=remote_addr,
            event_long='Duplicate secondary nonce',
        )
        return flask.abort(415)

    key_data = json.loads(plaintext)

    client_platform = utils.filter_str(key_data['platform'])
    client_ver = utils.filter_str(key_data.get('client_ver'))
    client_device_id = utils.filter_str(key_data['device_id'])
    client_device_name = utils.filter_str(key_data['device_name'])
    client_device_hostname = utils.filter_str(
        key_data.get('device_hostname')) or client_device_name
    client_device_key64 = utils.filter_str(key_data.get('device_key'))
    client_mac_addr = utils.filter_str(key_data['mac_addr'])
    client_mac_addrs = key_data['mac_addrs']
    if client_mac_addrs:
        client_mac_addrs = [utils.filter_str(x)
            for x in client_mac_addrs]
    else:
        client_mac_addrs = None
    client_auth_token = key_data['token']
    client_auth_nonce = utils.filter_str(key_data['nonce'])
    client_auth_password = key_data['password']
    client_auth_timestamp = int(key_data['timestamp'])
    client_sso_token = key_data.get('sso_token')
    client_public_address = utils.filter_str(key_data['public_address'])
    client_public_address6 = utils.filter_str(key_data['public_address6'])

    if client_public_address:
        client_public_address = str(ipaddress.IPv4Address(
            client_public_address))
    else:
        client_public_address = None

    if client_public_address6:
        client_public_address6 = str(ipaddress.IPv6Address(
            client_public_address6))
    else:
        client_public_address6 = None

    if ':' in remote_addr:
        remote_addr = str(ipaddress.IPv6Address(remote_addr))
    else:
        remote_addr = str(ipaddress.IPv4Address(remote_addr))

    if svr.device_auth:
        if not client_device_key64 or not device_signature64:
            journal.entry(
                journal.USER_WG_FAILURE,
                usr.journal_data,
                remote_address=remote_addr,
                event_long='Invalid device signature',
            )
            return utils.jsonify({
                'error': 'device_signature_missing',
                'error_msg': 'Device signature missing.',
            }, 400)

        try:
            usr.device_verify_sig(
                client_device_hostname,
                client_platform,
                utils.base64raw_decode(client_device_key64),
                data_hash,
                utils.base64raw_decode(device_signature64),
            )

            journal.entry(
                journal.USER_DEVICE_AUTHENTICATE_SUCCESS,
                usr.journal_data,
                device_name=client_device_hostname,
                device_platform=client_platform,
                device_public_key=client_device_key64,
                remote_address=remote_addr,
                event_long='User verified device signature',
            )
        except DeviceUnregistered as err:
            send_data = {
                'allow': False,
                'token': None,
                'reason': None,
                'reg_key': err.reg_key,
                'remote': settings.local.host.public_addr,
                'remote6': settings.local.host.public_addr6,
            }

            send_nonce = nacl.utils.random(nacl.public.Box.NONCE_SIZE)
            nacl_box = nacl.public.Box(priv_key, sender_pub_key)
            send_cipher_data = nacl_box.encrypt(
                json.dumps(send_data).encode(), send_nonce)
            send_cipher_data = send_cipher_data[nacl.public.Box.NONCE_SIZE:]

            send_nonce64 = base64.b64encode(send_nonce).decode()
            send_cipher_data64 = base64.b64encode(send_cipher_data).decode()

            usr.audit_event('user_profile',
                'User device registration required',
                remote_addr=remote_addr,
            )

            journal.entry(
                journal.USER_DEVICE_CREATE,
                usr.journal_data,
                device_name=client_device_hostname,
                device_platform=client_platform,
                device_public_key=client_device_key64,
                remote_address=remote_addr,
                event_long='Device registration required',
            )

            journal.entry(
                journal.USER_OVPN_FAILURE,
                usr.journal_data,
                remote_address=remote_addr,
                event_long='Device registration required',
            )

            sync_signature = base64.b64encode(hmac.new(
                usr.sync_secret.encode(),
                (send_cipher_data64 + '&' + send_nonce64).encode(),
                hashlib.sha512).digest()).decode()

            return utils.jsonify({
                'data': send_cipher_data64,
                'nonce': send_nonce64,
                'signature': sync_signature,
            })
        except InvalidSignature:
            journal.entry(
                journal.USER_DEVICE_AUTHENTICATE_FAILURE,
                usr.journal_data,
                device_name=client_device_hostname,
                device_platform=client_platform,
                device_public_key=client_device_key64,
                remote_address=remote_addr,
                event_long='User device signature invalid',
            )
            journal.entry(
                journal.USER_WG_FAILURE,
                usr.journal_data,
                remote_address=remote_addr,
                event_long='Invalid device signature',
            )
            return utils.jsonify({
                'error': 'device_signature_invalid',
                'error_msg': 'Device signature invalid.',
            }, 400)

    instance = server.get_instance(server_id)
    if not instance or instance.state != 'running':
        return flask.abort(429)

    if not instance.server.sso_auth:
        return flask.abort(431)

    clients = instance.instance_com.clients

    sso_token = None
    if client_sso_token:
        authorized = False

        for i in range(100):
            if sso.check_token(client_sso_token, usr.id, svr.id):
                authorized = True
                break
            time.sleep(0.2)

        if not authorized:
            return flask.abort(428)
        sso_token = client_sso_token

    event = threading.Event()
    send_data = {
        'allow': None,
        'token': None,
        'reason': None,
        'remote': settings.local.host.public_addr,
        'remote6': settings.local.host.public_addr6,
    }
    def callback(allow, data):
        send_data['allow'] = allow
        if allow:
            send_data['token'] = data
        else:
            send_data['reason'] = data
        event.set()

    clients.open_ovpn(
        user=usr,
        org=org,
        auth_password=client_auth_password,
        auth_token=client_auth_token,
        auth_nonce=client_auth_nonce,
        auth_timestamp=client_auth_timestamp,
        sso_token=sso_token,
        platform=client_platform,
        client_ver=client_ver,
        device_id=client_device_id,
        device_name=client_device_name,
        mac_addr=client_mac_addr,
        mac_addrs=client_mac_addrs,
        client_public_address=client_public_address,
        client_public_address6=client_public_address6,
        remote_ip=remote_addr,
        connect_callback=callback,
    )

    event.wait()

    send_nonce = nacl.utils.random(nacl.public.Box.NONCE_SIZE)
    nacl_box = nacl.public.Box(priv_key, sender_pub_key)
    send_cipher_data = nacl_box.encrypt(
        json.dumps(send_data).encode(), send_nonce)
    send_cipher_data = send_cipher_data[nacl.public.Box.NONCE_SIZE:]

    send_nonce64 = base64.b64encode(send_nonce).decode()
    send_cipher_data64 = base64.b64encode(send_cipher_data).decode()

    usr.audit_event('user_profile',
        'User opened ovpn connection from pritunl client',
        remote_addr=remote_addr,
    )

    journal.entry(
        journal.USER_OVPN_SUCCESS,
        usr.journal_data,
        remote_address=remote_addr,
        event_long='User opened ovpn connection from pritunl client',
    )

    sync_signature = base64.b64encode(hmac.new(
        usr.sync_secret.encode(),
        (send_cipher_data64 + '&' + send_nonce64).encode(),
        hashlib.sha512).digest()).decode()

    return utils.jsonify({
        'data': send_cipher_data64,
        'nonce': send_nonce64,
        'signature': sync_signature,
    })

@app.app.route('/key/wg_wait/<org_id>/<user_id>/<server_id>',
    methods=['POST'])
@auth.open_auth
def key_wg_wait_post(org_id, user_id, server_id):
    org_id = org_id
    user_id = user_id
    server_id = server_id
    remote_addr = utils.get_remote_addr()

    auth_token = flask.request.headers.get('Auth-Token', None)
    auth_timestamp = flask.request.headers.get('Auth-Timestamp', None)
    auth_nonce = flask.request.headers.get('Auth-Nonce', None)
    auth_signature = flask.request.headers.get('Auth-Signature', None)
    if not auth_token or not auth_timestamp or not auth_nonce or \
        not auth_signature:
        journal.entry(
            journal.USER_WG_FAILURE,
            remote_address=remote_addr,
            event_long='Missing auth header',
        )
        return flask.abort(406)
    auth_token = auth_token[:256]
    auth_timestamp = auth_timestamp[:64]
    auth_nonce = auth_nonce[:32]
    auth_signature = auth_signature[:512]

    try:
        if abs(int(auth_timestamp) - int(utils.time_now())) > \
            settings.app.auth_time_window:
            journal.entry(
                journal.USER_WG_FAILURE,
                remote_address=remote_addr,
                event_long='Expired auth timestamp',
            )
            return flask.abort(408)
    except ValueError:
        journal.entry(
            journal.USER_WG_FAILURE,
            remote_address=remote_addr,
            event_long='Invalid auth timestamp',
        )
        return flask.abort(405)

    org = organization.get_by_id(org_id)
    if not org:
        journal.entry(
            journal.USER_WG_FAILURE,
            remote_address=remote_addr,
            event_long='Organization not found',
        )
        return flask.abort(404)

    usr = org.get_user(id=user_id)
    if not usr:
        journal.entry(
            journal.USER_WG_FAILURE,
            remote_address=remote_addr,
            event_long='User not found',
        )
        return flask.abort(404)
    elif not usr.sync_secret:
        journal.entry(
            journal.USER_WG_FAILURE,
            usr.journal_data,
            remote_address=remote_addr,
            event_long='User missing sync secret',
        )
        return flask.abort(410)

    if auth_token != usr.sync_token:
        journal.entry(
            journal.USER_WG_FAILURE,
            usr.journal_data,
            remote_address=remote_addr,
            event_long='Sync token mismatch',
        )
        return flask.abort(411)

    if usr.disabled:
        journal.entry(
            journal.USER_WG_FAILURE,
            usr.journal_data,
            remote_address=remote_addr,
            event_long='User disabled',
        )
        return flask.abort(403)

    cipher_data64 = flask.request.json.get('data')
    box_nonce64 = flask.request.json.get('nonce')
    public_key64 = flask.request.json.get('public_key')
    signature64 = flask.request.json.get('signature')
    device_signature64 = flask.request.json.get('device_signature')

    auth_string = '&'.join([
        usr.sync_token, auth_timestamp, auth_nonce, flask.request.method,
        flask.request.path, cipher_data64, box_nonce64, public_key64,
        signature64] + ([device_signature64] if device_signature64 else []))

    if len(auth_string) > AUTH_SIG_STRING_MAX_LEN:
        journal.entry(
            journal.USER_WG_FAILURE,
            usr.journal_data,
            remote_address=remote_addr,
            event_long='Auth string len limit exceeded',
        )
        return flask.abort(414)

    auth_test_signature = base64.b64encode(hmac.new(
        usr.sync_secret.encode(), auth_string.encode(),
        hashlib.sha512).digest()).decode()
    if not utils.const_compare(auth_signature, auth_test_signature):
        journal.entry(
            journal.USER_WG_FAILURE,
            usr.journal_data,
            remote_address=remote_addr,
            event_long='Auth signature mismatch',
        )
        return flask.abort(401)

    nonces_collection = mongo.get_collection('auth_nonces')
    try:
        nonces_collection.insert_one({
            'token': auth_token,
            'nonce': auth_nonce,
            'timestamp': utils.now(),
        })
    except pymongo.errors.DuplicateKeyError:
        journal.entry(
            journal.USER_WG_FAILURE,
            usr.journal_data,
            remote_address=remote_addr,
            event_long='Duplicate nonce from reconnection',
        )
        return flask.abort(409)

    data_hash = hashlib.sha512(
        '&'.join([cipher_data64, box_nonce64, public_key64]).encode(),
    ).digest()
    try:
        usr.verify_sig(
            data_hash,
            base64.b64decode(signature64),
        )
    except InvalidSignature:
        journal.entry(
            journal.USER_WG_FAILURE,
            usr.journal_data,
            remote_address=remote_addr,
            event_long='Invalid rsa signature',
        )
        return flask.abort(412)

    svr = usr.get_server(server_id)

    sender_pub_key = nacl.public.PublicKey(
        base64.b64decode(public_key64))
    box_nonce = base64.b64decode(box_nonce64)

    priv_key = nacl.public.PrivateKey(
        base64.b64decode(svr.auth_box_private_key))

    cipher_data = base64.b64decode(cipher_data64)
    nacl_box = nacl.public.Box(priv_key, sender_pub_key)
    plaintext = nacl_box.decrypt(cipher_data, box_nonce).decode()

    try:
        nonces_collection.insert_one({
            'token': auth_token,
            'nonce': box_nonce64,
            'timestamp': utils.now(),
        })
    except pymongo.errors.DuplicateKeyError:
        journal.entry(
            journal.USER_WG_FAILURE,
            usr.journal_data,
            remote_address=remote_addr,
            event_long='Duplicate secondary nonce',
        )
        return flask.abort(415)

    key_data = json.loads(plaintext)

    client_platform = utils.filter_str(key_data['platform'])
    client_ver = utils.filter_str(key_data.get('client_ver'))
    client_device_id = utils.filter_str(key_data['device_id'])
    client_device_name = utils.filter_str(key_data['device_name'])
    client_device_hostname = utils.filter_str(
        key_data.get('device_hostname')) or client_device_name
    client_device_key64 = utils.filter_str(key_data.get('device_key'))
    client_mac_addr = utils.filter_str(key_data['mac_addr'])
    client_mac_addrs = key_data['mac_addrs']
    if client_mac_addrs:
        client_mac_addrs = [utils.filter_str(x)
            for x in client_mac_addrs]
    else:
        client_mac_addrs = None
    client_auth_token = key_data['token']
    client_auth_nonce = utils.filter_str(key_data['nonce'])
    client_auth_password = key_data['password']
    client_auth_timestamp = int(key_data['timestamp'])
    client_sso_token = key_data.get('sso_token')
    client_public_address = utils.filter_str(
        key_data.get('public_address'))
    client_public_address6 = utils.filter_str(
        key_data.get('public_address6'))
    client_wg_public_key = key_data['wg_public_key']

    if client_public_address:
        client_public_address = str(ipaddress.IPv4Address(
            client_public_address))
    else:
        client_public_address = None

    if client_public_address6:
        client_public_address6 = str(ipaddress.IPv6Address(
            client_public_address6))
    else:
        client_public_address6 = None

    if ':' in remote_addr:
        remote_addr = str(ipaddress.IPv6Address(remote_addr))
    else:
        remote_addr = str(ipaddress.IPv4Address(remote_addr))

    if len(client_wg_public_key) < 32:
        journal.entry(
            journal.USER_WG_FAILURE,
            usr.journal_data,
            remote_address=remote_addr,
            event_long='Public key too short',
        )
        return flask.abort(416)

    try:
        client_wg_public_key = base64.b64decode(client_wg_public_key)
        if len(client_wg_public_key) != 32:
            raise ValueError('Invalid length')
        client_wg_public_key = base64.b64encode(
            client_wg_public_key).decode()
    except:
        journal.entry(
            journal.USER_WG_FAILURE,
            usr.journal_data,
            remote_address=remote_addr,
            event_long='Public key invalid',
        )
        return flask.abort(417)

    if svr.device_auth:
        if not client_device_key64 or not device_signature64:
            journal.entry(
                journal.USER_WG_FAILURE,
                usr.journal_data,
                remote_address=remote_addr,
                event_long='Invalid device signature',
            )
            return utils.jsonify({
                'error': 'device_signature_missing',
                'error_msg': 'Device signature missing.',
            }, 400)

        try:
            usr.device_verify_sig(
                client_device_hostname,
                client_platform,
                utils.base64raw_decode(client_device_key64),
                data_hash,
                utils.base64raw_decode(device_signature64),
            )

            journal.entry(
                journal.USER_DEVICE_AUTHENTICATE_SUCCESS,
                usr.journal_data,
                device_name=client_device_hostname,
                device_platform=client_platform,
                device_public_key=client_device_key64,
                remote_address=remote_addr,
                event_long='User verified device signature',
            )
        except DeviceUnregistered as err:
            send_data = {
                'allow': False,
                'token': None,
                'reason': None,
                'reg_key': err.reg_key,
                'remote': settings.local.host.public_addr,
                'remote6': settings.local.host.public_addr6,
            }

            send_nonce = nacl.utils.random(nacl.public.Box.NONCE_SIZE)
            nacl_box = nacl.public.Box(priv_key, sender_pub_key)
            send_cipher_data = nacl_box.encrypt(
                json.dumps(send_data).encode(), send_nonce)
            send_cipher_data = send_cipher_data[nacl.public.Box.NONCE_SIZE:]

            send_nonce64 = base64.b64encode(send_nonce).decode()
            send_cipher_data64 = base64.b64encode(send_cipher_data).decode()

            usr.audit_event('user_profile',
                'User device registration required',
                remote_addr=remote_addr,
            )

            journal.entry(
                journal.USER_DEVICE_CREATE,
                usr.journal_data,
                device_name=client_device_hostname,
                device_platform=client_platform,
                device_public_key=client_device_key64,
                remote_address=remote_addr,
                event_long='New user device request',
            )

            journal.entry(
                journal.USER_WG_FAILURE,
                usr.journal_data,
                remote_address=remote_addr,
                event_long='Device registration required',
            )

            sync_signature = base64.b64encode(hmac.new(
                usr.sync_secret.encode(),
                (send_cipher_data64 + '&' + send_nonce64).encode(),
                hashlib.sha512).digest()).decode()

            return utils.jsonify({
                'data': send_cipher_data64,
                'nonce': send_nonce64,
                'signature': sync_signature,
            })
        except InvalidSignature:
            journal.entry(
                journal.USER_DEVICE_AUTHENTICATE_FAILURE,
                usr.journal_data,
                device_name=client_device_name,
                device_platform=client_platform,
                device_public_key=client_device_key64,
                remote_address=remote_addr,
                event_long='User device signature invalid',
            )
            journal.entry(
                journal.USER_WG_FAILURE,
                usr.journal_data,
                device_name=client_device_name,
                device_platform=client_platform,
                device_public_key=client_device_key64,
                remote_address=remote_addr,
                event_long='Invalid device signature',
            )
            return utils.jsonify({
                'error': 'device_signature_invalid',
                'error_msg': 'Device signature invalid.',
            }, 400)

    instance = server.get_instance(server_id)
    if not instance or instance.state != 'running':
        return flask.abort(429)

    if not instance.server.sso_auth:
        return flask.abort(431)

    if not instance.server.wg:
        return flask.abort(429)

    sso_token = None
    if client_sso_token:
        authorized = False

        for i in range(100):
            if sso.check_token(client_sso_token, usr.id, svr.id):
                authorized = True
                break
            time.sleep(0.2)

        if not authorized:
            return flask.abort(428)
        sso_token = client_sso_token

    wg_keys_collection = mongo.get_collection('wg_keys')
    try:
        wg_keys_collection.insert_one({
            '_id': client_wg_public_key,
            'timestamp': utils.now(),
        })
    except pymongo.errors.DuplicateKeyError:
        journal.entry(
            journal.USER_WG_FAILURE,
            usr.journal_data,
            remote_address=remote_addr,
            wg_public_key=client_wg_public_key,
            event_long='Duplicate wg public key',
        )
        return flask.abort(413)

    clients = instance.instance_com.clients

    event = threading.Event()
    send_data = {
        'allow': None,
        'configuration': None,
        'reason': None,
    }
    def callback(allow, data):
        send_data['allow'] = allow
        if allow:
            send_data['configuration'] = data
        else:
            send_data['reason'] = data
        event.set()

    clients.connect_wg(
        user=usr,
        org=org,
        wg_public_key=client_wg_public_key,
        auth_password=client_auth_password,
        auth_token=client_auth_token,
        auth_nonce=client_auth_nonce,
        auth_timestamp=client_auth_timestamp,
        sso_token=sso_token,
        platform=client_platform,
        client_ver=client_ver,
        device_id=client_device_id,
        device_name=client_device_name,
        mac_addr=client_mac_addr,
        mac_addrs=client_mac_addrs,
        client_public_address=client_public_address,
        client_public_address6=client_public_address6,
        remote_ip=remote_addr,
        connect_callback=callback,
    )

    event.wait()

    send_nonce = nacl.utils.random(nacl.public.Box.NONCE_SIZE)
    nacl_box = nacl.public.Box(priv_key, sender_pub_key)
    send_cipher_data = nacl_box.encrypt(
        json.dumps(send_data).encode(), send_nonce)
    send_cipher_data = send_cipher_data[nacl.public.Box.NONCE_SIZE:]

    send_nonce64 = base64.b64encode(send_nonce).decode()
    send_cipher_data64 = base64.b64encode(send_cipher_data).decode()

    usr.audit_event('user_profile',
        'User retrieved wg public key from pritunl client',
        remote_addr=remote_addr,
    )

    journal.entry(
        journal.USER_WG_SUCCESS,
        usr.journal_data,
        remote_address=remote_addr,
        event_long='User retrieved wg public key from pritunl client',
    )

    sync_signature = base64.b64encode(hmac.new(
        usr.sync_secret.encode(),
        (send_cipher_data64 + '&' + send_nonce64).encode(),
        hashlib.sha512).digest()).decode()

    return utils.jsonify({
        'data': send_cipher_data64,
        'nonce': send_nonce64,
        'signature': sync_signature,
    })
