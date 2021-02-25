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
import nacl.public
from cryptography.exceptions import InvalidSignature

def _get_key_tar_archive(org_id, user_id):
    org = organization.get_by_id(org_id)
    usr = org.get_user(user_id)
    key_archive = usr.build_key_tar_archive()
    response = flask.Response(response=key_archive,
        mimetype='application/octet-stream')
    response.headers.add('Content-Disposition',
        'attachment; filename="%s.tar"' % usr.name)
    return (usr, response)

def _get_key_zip_archive(org_id, user_id):
    org = organization.get_by_id(org_id)
    usr = org.get_user(user_id)
    key_archive = usr.build_key_zip_archive()
    response = flask.Response(response=key_archive,
        mimetype='application/octet-stream')
    response.headers.add('Content-Disposition',
        'attachment; filename="%s_%s.zip"' % (org.name, usr.name))
    return (usr, response)

def _get_onc_archive(org_id, user_id):
    org = organization.get_by_id(org_id)
    usr = org.get_user(user_id)
    onc_conf = usr.build_onc()
    response = flask.Response(response=onc_conf,
        mimetype='application/x-onc')
    response.headers.add('Content-Disposition',
        'attachment; filename="%s_%s.onc"' % (org.name, usr.name))
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

        response = collection.update({
            '_id': doc['_id'],
            'short_id': doc['short_id'],
            'one_time': True,
        }, {'$set': set_doc})
        if not response['updatedExisting']:
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

    if org.otp_auth and not usr.has_duo_passcode and not usr.has_yubikey:
        key_page = key_page.replace('<%= user_otp_key %>', usr.otp_secret)
        key_page = key_page.replace('<%= user_otp_url %>',
            'otpauth://totp/%s@%s?secret=%s' % (
                usr.name, org.name, usr.otp_secret))
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
    collection.remove({
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
        nonces_collection.insert({
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

    auth_string = '&'.join([
        usr.sync_token, auth_timestamp, auth_nonce, flask.request.method,
        flask.request.path, cipher_data64, box_nonce64, public_key64,
        signature64])

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
        nonces_collection.insert({
            'token': auth_token,
            'nonce': auth_nonce,
            'timestamp': utils.now(),
        })
    except pymongo.errors.DuplicateKeyError:
        journal.entry(
            journal.USER_WG_FAILURE,
            usr.journal_data,
            remote_address=remote_addr,
            event_long='Duplicate nonce',
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
        nonces_collection.insert({
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
    client_device_id = utils.filter_str(key_data['device_id'])
    client_device_name = utils.filter_str(key_data['device_name'])
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
    client_wg_public_key = key_data['wg_public_key']

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
        client_wg_public_key = base64.b64encode(client_wg_public_key)
    except:
        journal.entry(
            journal.USER_WG_FAILURE,
            usr.journal_data,
            remote_address=remote_addr,
            event_long='Public key invalid',
        )
        return flask.abort(417)

    instance = server.get_instance(server_id)
    if not instance or instance.state != 'running':
        return flask.abort(429)

    if not instance.server.wg:
        return flask.abort(429)

    wg_keys_collection = mongo.get_collection('wg_keys')
    try:
        wg_keys_collection.insert({
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
        platform=client_platform,
        device_id=client_device_id,
        device_name=client_device_name,
        mac_addr=client_mac_addr,
        mac_addrs=client_mac_addrs,
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
        nonces_collection.insert({
            'token': auth_token,
            'nonce': auth_nonce,
            'timestamp': utils.now(),
        })
    except pymongo.errors.DuplicateKeyError:
        journal.entry(
            journal.USER_WG_FAILURE,
            usr.journal_data,
            remote_address=remote_addr,
            event_long='Duplicate nonce',
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
        nonces_collection.insert({
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
        client_wg_public_key = base64.b64encode(client_wg_public_key)
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
        remote_ip=remote_addr,
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
