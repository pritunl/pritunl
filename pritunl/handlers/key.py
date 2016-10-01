from pritunl.constants import *
from pritunl.exceptions import *
from pritunl import utils
from pritunl import static
from pritunl import organization
from pritunl import settings
from pritunl import app
from pritunl import auth
from pritunl import mongo
from pritunl import sso
from pritunl import event
from pritunl import logger

import flask
import time
import pymongo
import hmac
import hashlib
import base64
import urlparse
import requests

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
        'attachment; filename="%s.zip"' % usr.name)
    return (usr, response)

def _get_onc_archive(org_id, user_id):
    org = organization.get_by_id(org_id)
    usr = org.get_user(user_id)
    key_archive = usr.build_onc_archive()
    response = flask.Response(response=key_archive,
        mimetype='application/octet-stream')
    response.headers.add('Content-Disposition',
        'attachment; filename="%s.zip"' % usr.name)
    return (usr, response)

def _find_doc(query, one_time=None, one_time_new=False):
    utils.rand_sleep()

    collection = mongo.get_collection('users_key_link')
    doc = collection.find_one(query)

    if one_time and doc and doc.get('one_time'):
        short_id = utils.generate_short_id()
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
    usr, resp = _get_key_tar_archive(org_id, user_id)

    usr.audit_event('user_profile',
        'User tar profile downloaded from web console',
        remote_addr=utils.get_remote_addr(),
    )

    return resp

@app.app.route('/key/<org_id>/<user_id>.zip', methods=['GET'])
@auth.session_light_auth
def user_key_zip_archive_get(org_id, user_id):
    usr, resp = _get_key_zip_archive(org_id, user_id)

    usr.audit_event('user_profile',
        'User zip profile downloaded from web console',
        remote_addr=utils.get_remote_addr(),
    )

    return resp

@app.app.route('/key_onc/<org_id>/<user_id>.zip', methods=['GET'])
@auth.session_light_auth
def user_key_onc_archive_get(org_id, user_id):
    usr, resp = _get_onc_archive(org_id, user_id)

    usr.audit_event('user_profile',
        'User onc profile downloaded from web console',
        remote_addr=utils.get_remote_addr(),
    )

    return resp

@app.app.route('/key/<org_id>/<user_id>', methods=['GET'])
@auth.session_auth
def user_key_link_get(org_id, user_id):
    org = organization.get_by_id(org_id)
    usr = org.get_user(user_id)

    usr.audit_event('user_profile',
        'User temporary profile links created from web console',
        remote_addr=utils.get_remote_addr(),
    )

    return utils.jsonify(org.create_user_key_link(user_id))

@app.app.route('/key/<org_id>/<user_id>/<server_id>.key', methods=['GET'])
@auth.session_light_auth
def user_linked_key_conf_get(org_id, user_id, server_id):
    org = organization.get_by_id(org_id)
    usr = org.get_user(user_id)
    key_conf = usr.build_key_conf(server_id)

    usr.audit_event('user_profile',
        'User key profile downloaded from web console',
        remote_addr=utils.get_remote_addr(),
    )

    response = flask.Response(response=key_conf['conf'],
        mimetype='application/ovpn')
    response.headers.add('Content-Disposition',
        'attachment; filename="%s"' % key_conf['name'])

    return response

@app.app.route('/key/<key_id>.tar', methods=['GET'])
@auth.open_auth
def user_linked_key_tar_archive_get(key_id):
    doc = _find_doc({
        'key_id': key_id,
    })
    if not doc:
        return flask.abort(404)

    usr, resp = _get_key_tar_archive(doc['org_id'], doc['user_id'])
    if usr.disabled:
        return flask.abort(403)

    usr.audit_event('user_profile',
        'User tar profile downloaded with temporary profile link',
        remote_addr=utils.get_remote_addr(),
    )

    return resp

@app.app.route('/key/<key_id>.zip', methods=['GET'])
@auth.open_auth
def user_linked_key_zip_archive_get(key_id):
    doc = _find_doc({
        'key_id': key_id,
    })
    if not doc:
        return flask.abort(404)

    usr, resp = _get_key_zip_archive(doc['org_id'], doc['user_id'])
    if usr.disabled:
        return flask.abort(403)

    usr.audit_event('user_profile',
        'User zip profile downloaded with temporary profile link',
        remote_addr=utils.get_remote_addr(),
    )

    return resp

@app.app.route('/key_onc/<key_id>.zip', methods=['GET'])
@auth.open_auth
def user_linked_key_onc_archive_get(key_id):
    doc = _find_doc({
        'key_id': key_id,
    })
    if not doc:
        return flask.abort(404)

    usr, resp = _get_onc_archive(doc['org_id'], doc['user_id'])
    if usr.disabled:
        return flask.abort(403)

    usr.audit_event('user_profile',
        'User onc profile downloaded with temporary profile link',
        remote_addr=utils.get_remote_addr(),
    )

    return resp

@app.app.route('/key_pin/<key_id>', methods=['PUT'])
@auth.open_auth
def user_key_pin_put(key_id):
    if settings.app.demo_mode:
        return utils.demo_blocked()

    doc = _find_doc({
        'key_id': key_id,
    })
    if not doc:
        return flask.abort(404)

    if settings.app.demo_mode:
        return utils.demo_blocked()

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

    if usr.pin and not usr.check_pin(current_pin):
        return utils.jsonify({
            'error': PIN_INVALID,
            'error_msg': PIN_INVALID_MSG,
        }, 400)

    if usr.set_pin(pin):
        usr.audit_event('user_updated',
            'User pin changed with temporary profile link',
            remote_addr=utils.get_remote_addr(),
        )

    usr.commit()

    event.Event(type=USERS_UPDATED, resource_id=org.id)

    return utils.jsonify({})

@app.app.route('/k/<short_code>', methods=['GET'])
@auth.open_auth
def user_linked_key_page_get(short_code):
    doc = _find_doc({
        'short_id': short_code,
    }, one_time=True, one_time_new=True)
    if not doc:
        return flask.abort(404)

    org = organization.get_by_id(doc['org_id'])
    user = org.get_user(id=doc['user_id'])
    if user.disabled:
        return flask.abort(403)

    user.audit_event('user_profile',
        'User temporary profile link viewed',
        remote_addr=utils.get_remote_addr(),
    )

    if settings.local.sub_active and settings.app.theme == 'dark':
        view_name = KEY_VIEW_DARK_NAME
    else:
        view_name = KEY_VIEW_NAME

    if RADIUS_AUTH in user.auth_type or \
            settings.user.pin_mode == PIN_DISABLED:
        header_class = 'pin-disabled'
    else:
        header_class = ''

    key_page = static.StaticFile(settings.conf.www_path, view_name,
        cache=False, gzip=False).data
    key_page = key_page.replace('<%= header_class %>', header_class)

    uri_url = (utils.get_url_root() + '/ku/' + doc['short_id']).encode()
    if uri_url.startswith('https'):
        uri_url = uri_url.replace('https', 'pritunl', 1)
    else:
        uri_url = uri_url.replace('http', 'pritunl', 1)
    key_page = key_page.replace('<%= uri_url %>', uri_url)

    key_page = key_page.replace('<%= user_name %>', '%s - %s' % (
        org.name, user.name))
    key_page = key_page.replace('<%= user_key_tar_url %>', '/key/%s.tar' % (
        doc['key_id']))
    key_page = key_page.replace('<%= user_key_zip_url %>', '/key/%s.zip' % (
        doc['key_id']))

    if org.otp_auth:
        key_page = key_page.replace('<%= user_otp_key %>', user.otp_secret)
        key_page = key_page.replace('<%= user_otp_url %>',
            'otpauth://totp/%s@%s?secret=%s' % (
                user.name, org.name, user.otp_secret))
    else:
        key_page = key_page.replace('<%= user_otp_key %>', '')
        key_page = key_page.replace('<%= user_otp_url %>', '')

    if user.pin:
        key_page = key_page.replace('<%= cur_pin_display %>', 'block')
    else:
        key_page = key_page.replace('<%= cur_pin_display %>', 'none')

    key_page = key_page.replace('<%= key_id %>', doc['key_id'])
    key_page = key_page.replace('<%= short_id %>', doc['short_id'])

    conf_links = ''

    if settings.local.sub_active:
        conf_links += '<a class="btn btn-success" ' + \
            'title="Download Chromebook Profiles" ' + \
            'href="/key_onc/%s.zip">Download Chromebook Profiles</a><br>\n' % (
                doc['key_id'])

    for server in user.iter_servers():
        conf_links += '<a class="btn btn-sm" title="Download Profile" ' + \
            'href="/key/%s/%s.key">Download Profile (%s)</a><br>\n' % (
                doc['key_id'], server.id, server.name)
    key_page = key_page.replace('<%= conf_links %>', conf_links)

    return key_page

@app.app.route('/k/<short_code>', methods=['DELETE'])
@auth.open_auth
def user_linked_key_page_delete_get(short_code):
    utils.rand_sleep()

    collection = mongo.get_collection('users_key_link')
    collection.remove({
        'short_id': short_code,
    })

    return utils.jsonify({})

@app.app.route('/ku/<short_code>', methods=['GET'])
@auth.open_auth
def user_uri_key_page_get(short_code):
    doc = _find_doc({
        'short_id': short_code,
    }, one_time=True)
    if not doc:
        return flask.abort(404)

    org = organization.get_by_id(doc['org_id'])
    user = org.get_user(id=doc['user_id'])
    if user.disabled:
        return flask.abort(403)

    user.audit_event('user_profile',
        'User temporary profile downloaded from pritunl client',
        remote_addr=utils.get_remote_addr(),
    )

    keys = {}
    for server in user.iter_servers():
        key = user.build_key_conf(server.id)
        keys[key['name']] = key['conf']

    return utils.jsonify(keys)

@app.app.route('/key/<key_id>/<server_id>.key', methods=['GET'])
@auth.open_auth
def user_linked_key_conf_get(key_id, server_id):
    doc = _find_doc({
        'key_id': key_id,
    })
    if not doc:
        return flask.abort(404)

    org = organization.get_by_id(doc['org_id'])
    if not org:
        return flask.abort(404)

    user = org.get_user(id=doc['user_id'])
    if not user:
        return flask.abort(404)

    if user.disabled:
        return flask.abort(403)

    key_conf = user.build_key_conf(server_id)

    user.audit_event('user_profile',
        'User profile downloaded with temporary profile link',
        remote_addr=utils.get_remote_addr(),
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
    utils.rand_sleep()

    if not settings.local.sub_active:
        return utils.response('', status_code=480)

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

    org = organization.get_by_id(org_id)
    if not org:
        return flask.abort(401)

    user = org.get_user(id=user_id)
    if not user:
        return flask.abort(401)
    elif not user.sync_secret:
        return flask.abort(401)

    if auth_token != user.sync_token:
        return flask.abort(401)

    if user.disabled:
        return flask.abort(403)

    auth_string = '&'.join([
        user.sync_token, auth_timestamp, auth_nonce, flask.request.method,
        flask.request.path] +
        ([flask.request.data] if flask.request.data else []))

    if len(auth_string) > AUTH_SIG_STRING_MAX_LEN:
        return flask.abort(401)

    auth_test_signature = base64.b64encode(hmac.new(
        user.sync_secret.encode(), auth_string,
        hashlib.sha512).digest())
    if auth_signature != auth_test_signature:
        return flask.abort(401)

    nonces_collection = mongo.get_collection('auth_nonces')
    try:
        nonces_collection.insert({
            'token': auth_token,
            'nonce': auth_nonce,
            'timestamp': utils.now(),
        }, w=0)
    except pymongo.errors.DuplicateKeyError:
        return flask.abort(401)

    key_conf = user.sync_conf(server_id, key_hash)
    if key_conf:
        user.audit_event('user_profile',
            'User profile synced from pritunl client',
            remote_addr=utils.get_remote_addr(),
        )

        sync_signature = base64.b64encode(hmac.new(
            user.sync_secret.encode(), key_conf['conf'],
            hashlib.sha512).digest())

        return utils.jsonify({
            'signature': sync_signature,
            'conf': key_conf['conf'],
        })

    return utils.jsonify({})

@app.app.route('/sso/authenticate', methods=['POST'])
@auth.open_auth
def sso_authenticate_post():
    if settings.app.sso != DUO_AUTH:
        return flask.abort(405)

    username = flask.request.json['username']
    usernames = [username]
    email = None
    if '@' in username:
        email = username
        usernames.append(username.split('@')[0])

    valid = False
    org_id = None
    for i, username in enumerate(usernames):
        try:
            valid, org_id = sso.auth_duo(
                username,
                strong=True,
                ipaddr=utils.get_remote_addr(),
                type='Key',
            )
            break
        except InvalidUser:
            if i == len(usernames) - 1:
                logger.error('Invalid duo username', 'sso',
                    username=username,
                )

    if valid:
        valid, org_id_new, groups = sso.plugin_sso_authenticate(
            sso_type='duo',
            user_name=username,
            user_email=email,
            remote_ip=utils.get_remote_addr(),
        )
        org_id = org_id_new or org_id
        if not valid:
            logger.error('Duo plugin authentication not valid', 'sso',
                username=username,
            )
            return flask.abort(401)
    else:
        logger.error('Duo authentication not valid', 'sso',
            username=username,
        )
        return flask.abort(401)

    if not org_id:
        org_id = settings.app.sso_org

    org = organization.get_by_id(org_id)
    if not org:
        logger.error('Organization for Duo sso does not exist', 'sso',
            org_id=org_id,
        )
        return flask.abort(405)

    usr = org.find_user(name=username)
    if not usr:
        usr = org.new_user(name=username, email=email, type=CERT_CLIENT,
            auth_type=DUO_AUTH, groups=list(groups) if groups else None)
        usr.audit_event('user_created', 'User created with single sign-on',
            remote_addr=utils.get_remote_addr())

        event.Event(type=ORGS_UPDATED)
        event.Event(type=USERS_UPDATED, resource_id=org.id)
        event.Event(type=SERVERS_UPDATED)
    else:
        if usr.disabled:
            return flask.abort(403)

        if groups and groups - set(usr.groups or []):
            usr.groups = list(set(usr.groups or []) | groups)
            usr.commit('groups')

        if usr.auth_type != DUO_AUTH:
            usr.auth_type = DUO_AUTH
            usr.commit('auth_type')
            event.Event(type=USERS_UPDATED, resource_id=org.id)

    key_link = org.create_user_key_link(usr.id, one_time=True)

    usr.audit_event('user_profile',
        'User profile viewed from single sign-on',
        remote_addr=utils.get_remote_addr(),
    )

    return utils.get_url_root() + key_link['view_url']

@app.app.route('/sso/request', methods=['GET'])
@auth.open_auth
def sso_request_get():
    sso_mode = settings.app.sso

    if sso_mode not in (GOOGLE_AUTH, GOOGLE_DUO_AUTH, SLACK_AUTH,
            SLACK_DUO_AUTH, SAML_AUTH, SAML_DUO_AUTH, SAML_OKTA_AUTH,
            SAML_OKTA_DUO_AUTH, SAML_ONELOGIN_AUTH, SAML_ONELOGIN_DUO_AUTH):
        return flask.abort(404)

    state = utils.rand_str(64)
    secret = utils.rand_str(64)
    callback = utils.get_url_root() + '/sso/callback'

    if not settings.local.sub_active:
        logger.error('Subscription must be active for sso', 'sso')
        return flask.abort(405)

    if GOOGLE_AUTH in sso_mode:
        resp = requests.post(AUTH_SERVER + '/v1/request/google',
            headers={
                'Content-Type': 'application/json',
            },
            json={
                'license': settings.app.license,
                'callback': callback,
                'state': state,
                'secret': secret,
            }
        )

        if resp.status_code != 200:
            logger.error('Google auth server error', 'sso',
                status_code=resp.status_code,
                content=resp.content,
            )

            if resp.status_code == 401:
                return flask.abort(405)

            return flask.abort(500)

        tokens_collection = mongo.get_collection('sso_tokens')
        tokens_collection.insert({
            '_id': state,
            'type': GOOGLE_AUTH,
            'secret': secret,
            'timestamp': utils.now(),
        })

        data = resp.json()

        return utils.redirect(data['url'])

    elif SLACK_AUTH in sso_mode:
        resp = requests.post(AUTH_SERVER + '/v1/request/slack',
            headers={
                'Content-Type': 'application/json',
            },
            json={
                'license': settings.app.license,
                'callback': callback,
                'state': state,
                'secret': secret,
            }
        )

        if resp.status_code != 200:
            logger.error('Slack auth server error', 'sso',
                status_code=resp.status_code,
                content=resp.content,
            )

            if resp.status_code == 401:
                return flask.abort(405)

            return flask.abort(500)

        tokens_collection = mongo.get_collection('sso_tokens')
        tokens_collection.insert({
            '_id': state,
            'type': SLACK_AUTH,
            'secret': secret,
            'timestamp': utils.now(),
        })

        data = resp.json()

        return utils.redirect(data['url'])

    elif SAML_AUTH in sso_mode:
        resp = requests.post(AUTH_SERVER + '/v1/request/saml',
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

        tokens_collection = mongo.get_collection('sso_tokens')
        tokens_collection.insert({
            '_id': state,
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

@app.app.route('/sso/callback', methods=['GET'])
@auth.open_auth
def sso_callback_get():
    sso_mode = settings.app.sso

    if sso_mode not in (GOOGLE_AUTH, GOOGLE_DUO_AUTH, SLACK_AUTH,
            SLACK_DUO_AUTH, SAML_AUTH, SAML_DUO_AUTH, SAML_OKTA_AUTH,
            SAML_OKTA_DUO_AUTH, SAML_ONELOGIN_AUTH, SAML_ONELOGIN_DUO_AUTH):
        return flask.abort(405)

    state = flask.request.args.get('state')
    sig = flask.request.args.get('sig')

    tokens_collection = mongo.get_collection('sso_tokens')
    doc = tokens_collection.find_and_modify(query={
        '_id': state,
    }, remove=True)

    if not doc:
        return flask.abort(404)

    query = flask.request.query_string.split('&sig=')[0]
    test_sig = base64.urlsafe_b64encode(hmac.new(str(doc['secret']),
        query, hashlib.sha512).digest())

    if sig != test_sig:
        return flask.abort(401)

    params = urlparse.parse_qs(query)

    if doc.get('type') == SAML_AUTH:
        username = params.get('username')[0]
        email = params.get('email', [None])[0]
        org_name = params.get('org', [None])[0]

        if not username:
            return flask.abort(406)

        valid, org_name = sso.verify_saml(username, email, org_name)
        if not valid:
            return flask.abort(401)

        org_id = settings.app.sso_org
        if org_name:
            org = organization.get_by_name(org_name, fields=('_id'))
            if org:
                org_id = org.id

        valid, org_id_new, groups = sso.plugin_sso_authenticate(
            sso_type='saml',
            user_name=username,
            user_email=email,
            remote_ip=utils.get_remote_addr(),
            sso_org_names=[org_name],
        )
        if valid:
            org_id = org_id_new or org_id
        else:
            logger.error('Saml plugin authentication not valid', 'sso',
                username=username,
            )
            return flask.abort(401)
    elif doc.get('type') == SLACK_AUTH:
        username = params.get('username')[0]
        email = None
        user_team = params.get('team')[0]
        org_names = params.get('orgs', [''])[0]
        org_names = org_names.split(',')

        valid, org_name = sso.verify_slack(username, user_team, org_names)
        if not valid:
            return flask.abort(401)

        if org_name:
            org_names = [org_name]

        org_id = settings.app.sso_org
        for org_name in org_names:
            org = organization.get_by_name(org_name, fields=('_id'))
            if org:
                org_id = org.id
                break

        valid, org_id_new, groups = sso.plugin_sso_authenticate(
            sso_type='slack',
            user_name=username,
            user_email=email,
            remote_ip=utils.get_remote_addr(),
            sso_org_names=org_names,
        )
        if valid:
            org_id = org_id_new or org_id
        else:
            logger.error('Slack plugin authentication not valid', 'sso',
                username=username,
            )
            return flask.abort(401)
    else:
        username = params.get('username')[0]
        email = username

        valid, org_name = sso.verify_google(username)
        if not valid:
            return flask.abort(401)

        org_id = settings.app.sso_org
        if org_name:
            org = organization.get_by_name(org_name, fields=('_id'))
            if org:
                org_id = org.id

        valid, org_id_new, groups = sso.plugin_sso_authenticate(
            sso_type='google',
            user_name=username,
            user_email=email,
            remote_ip=utils.get_remote_addr(),
        )
        if valid:
            org_id = org_id_new or org_id
        else:
            logger.error('Google plugin authentication not valid', 'sso',
                username=username,
            )
            return flask.abort(401)

    if DUO_AUTH in sso_mode:
        valid, _ = sso.auth_duo(
            username,
            ipaddr=utils.get_remote_addr(),
            type='Key',
        )
        if valid:
            valid, org_id_new, groups2 = sso.plugin_sso_authenticate(
                sso_type='duo',
                user_name=username,
                user_email=email,
                remote_ip=utils.get_remote_addr(),
            )
            if valid:
                org_id = org_id_new or org_id
            else:
                logger.error('Duo plugin authentication not valid', 'sso',
                    username=username,
                )
                return flask.abort(401)

            groups = ((groups or set()) | (groups2 or set())) or None
        else:
            logger.error('Duo authentication not valid', 'sso',
                username=username,
            )
            return flask.abort(401)

    org = organization.get_by_id(org_id)
    if not org:
        return flask.abort(405)

    usr = org.find_user(name=username)
    if not usr:
        usr = org.new_user(name=username, email=email, type=CERT_CLIENT,
            auth_type=sso_mode, groups=list(groups) if groups else None)
        usr.audit_event('user_created', 'User created with single sign-on',
            remote_addr=utils.get_remote_addr())

        event.Event(type=ORGS_UPDATED)
        event.Event(type=USERS_UPDATED, resource_id=org.id)
        event.Event(type=SERVERS_UPDATED)
    else:
        if usr.disabled:
            return flask.abort(403)

        if groups and groups - set(usr.groups or []):
            usr.groups = list(set(usr.groups or []) | groups)
            usr.commit('groups')

        if usr.auth_type != sso_mode:
            usr.auth_type = sso_mode
            usr.commit('auth_type')

    key_link = org.create_user_key_link(usr.id, one_time=True)

    usr.audit_event('user_profile',
        'User profile viewed from single sign-on',
        remote_addr=utils.get_remote_addr(),
    )

    return utils.redirect(utils.get_url_root() + key_link['view_url'])
