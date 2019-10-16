from pritunl.constants import *
from pritunl.exceptions import *
from pritunl import utils
from pritunl import static
from pritunl import organization
from pritunl import user
from pritunl import settings
from pritunl import app
from pritunl import auth
from pritunl import mongo
from pritunl import sso
from pritunl import event
from pritunl import logger
from pritunl import journal

import flask
import hmac
import hashlib
import base64
import urlparse
import requests

def _validate_user(username, email, sso_mode, org_id, groups, remote_addr,
        http_redirect=False, yubico_id=None):
    usr = user.find_user_auth(name=username, auth_type=sso_mode)
    if not usr:
        org = organization.get_by_id(org_id)
        if not org:
            logger.error('Organization for sso does not exist', 'sso',
                org_id=org_id,
            )
            return flask.abort(405)

        usr = org.find_user(name=username)
    else:
        if usr.org_id != org_id:
            logger.info('User organization changed, moving user', 'sso',
                user_name=username,
                user_email=email,
                remote_ip=remote_addr,
                cur_org_id=usr.org_id,
                new_org_id=org_id,
            )

            org = organization.get_by_id(org_id)
            if not org:
                logger.error('Organization for sso does not exist', 'sso',
                    org_id=org_id,
                )
                return flask.abort(405)

            usr.remove()
            old_org_id = usr.org_id

            usr = org.new_user(
                name=usr.name,
                email=usr.email,
                type=usr.type,
                groups=usr.groups,
                auth_type=usr.auth_type,
                yubico_id=usr.yubico_id,
                disabled=usr.disabled,
                bypass_secondary=usr.bypass_secondary,
                client_to_client=usr.client_to_client,
                dns_servers=usr.dns_servers,
                dns_suffix=usr.dns_suffix,
                port_forwarding=usr.port_forwarding,
            )

            event.Event(type=ORGS_UPDATED)
            event.Event(type=USERS_UPDATED, resource_id=old_org_id)
            event.Event(type=USERS_UPDATED, resource_id=org.id)
            event.Event(type=SERVERS_UPDATED)

        org = usr.org

    if not usr:
        usr = org.new_user(name=username, email=email, type=CERT_CLIENT,
            auth_type=sso_mode, yubico_id=yubico_id,
            groups=list(groups) if groups else None)
        usr.audit_event('user_created', 'User created with single sign-on',
            remote_addr=remote_addr)

        journal.entry(
            journal.USER_CREATE,
            usr.journal_data,
            event_long='User created with single sign-on',
            remote_address=remote_addr,
        )

        event.Event(type=ORGS_UPDATED)
        event.Event(type=USERS_UPDATED, resource_id=org.id)
        event.Event(type=SERVERS_UPDATED)
    else:
        if yubico_id and usr.yubico_id and yubico_id != usr.yubico_id:
            journal.entry(
                journal.SSO_AUTH_FAILURE,
                user_name=username,
                remote_address=remote_addr,
                reason=journal.SSO_AUTH_REASON_INVALID_YUBIKEY,
                reason_long='Invalid username',
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

        if groups and groups - set(usr.groups or []):
            changed = True
            usr.groups = list(set(usr.groups or []) | groups)
            usr.commit('groups')

        if usr.auth_type != sso_mode:
            changed = True
            usr.auth_type = sso_mode
            usr.commit('auth_type')

        usr.clear_auth_cache()
        usr.disconnect()

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
        key_id_hash=hashlib.md5(key_link['id']).hexdigest(),
        remote_address=remote_addr,
    )

    journal.entry(
        journal.USER_PROFILE_SUCCESS,
        usr.journal_data,
        remote_address=remote_addr,
        event_long='User profile viewed from single sign-on',
    )

    if http_redirect:
        return utils.redirect(utils.get_url_root() + key_link['view_url'])
    else:
        return utils.jsonify({
            'redirect': utils.get_url_root() + key_link['view_url'],
        }, 200)

@app.app.route('/sso/authenticate', methods=['POST'])
@auth.open_auth
def sso_authenticate_post():
    if settings.app.sso != DUO_AUTH or \
            settings.app.sso_duo_mode == 'passcode':
        return flask.abort(405)

    remote_addr = utils.get_remote_addr()
    username = utils.json_filter_str('username')
    usernames = [username]
    email = None
    if '@' in username:
        email = username
        usernames.append(username.split('@')[0])

    valid = False
    for i, username in enumerate(usernames):
        try:
            duo_auth = sso.Duo(
                username=username,
                factor=settings.app.sso_duo_mode,
                remote_ip=remote_addr,
                auth_type='Key',
            )
            valid = duo_auth.authenticate()
            break
        except InvalidUser:
            if i == len(usernames) - 1:
                logger.warning('Invalid duo username', 'sso',
                    username=username,
                )

    if valid:
        valid, org_id, groups = sso.plugin_sso_authenticate(
            sso_type='duo',
            user_name=username,
            user_email=email,
            remote_ip=remote_addr,
        )
        if not valid:
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
        groups = set(groups or [])
    else:
        logger.warning('Duo authentication not valid', 'sso',
            username=username,
        )

        journal.entry(
            journal.SSO_AUTH_FAILURE,
            user_name=username,
            remote_address=remote_addr,
            reason=journal.SSO_AUTH_REASON_DUO_FAILED,
            reason_long='Duo authentication failed',
        )

        return flask.abort(401)

    if not org_id:
        org_id = settings.app.sso_org

    return _validate_user(username, email, DUO_AUTH, org_id, groups,
        remote_addr)

@app.app.route('/sso/request', methods=['GET'])
@auth.open_auth
def sso_request_get():
    sso_mode = settings.app.sso

    if sso_mode not in (AZURE_AUTH, AZURE_DUO_AUTH, AZURE_YUBICO_AUTH,
            GOOGLE_AUTH, GOOGLE_DUO_AUTH, GOOGLE_YUBICO_AUTH,
            AUTHZERO_AUTH, AUTHZERO_DUO_AUTH, AUTHZERO_YUBICO_AUTH,
            SLACK_AUTH, SLACK_DUO_AUTH, SLACK_YUBICO_AUTH, SAML_AUTH,
            SAML_DUO_AUTH, SAML_YUBICO_AUTH, SAML_OKTA_AUTH,
            SAML_OKTA_DUO_AUTH, SAML_OKTA_YUBICO_AUTH, SAML_ONELOGIN_AUTH,
            SAML_ONELOGIN_DUO_AUTH, SAML_ONELOGIN_YUBICO_AUTH):
        return flask.abort(404)

    state = utils.rand_str(64)
    secret = utils.rand_str(64)
    callback = utils.get_url_root() + '/sso/callback'
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

        tokens_collection = mongo.get_collection('sso_tokens')
        tokens_collection.insert({
            '_id': state,
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

        tokens_collection = mongo.get_collection('sso_tokens')
        tokens_collection.insert({
            '_id': state,
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

        tokens_collection = mongo.get_collection('sso_tokens')
        tokens_collection.insert({
            '_id': state,
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

    if sso_mode not in (AZURE_AUTH, AZURE_DUO_AUTH, AZURE_YUBICO_AUTH,
            GOOGLE_AUTH, GOOGLE_DUO_AUTH, GOOGLE_YUBICO_AUTH,
            AUTHZERO_AUTH, AUTHZERO_DUO_AUTH, AUTHZERO_YUBICO_AUTH,
            SLACK_AUTH, SLACK_DUO_AUTH, SLACK_YUBICO_AUTH, SAML_AUTH,
            SAML_DUO_AUTH, SAML_YUBICO_AUTH, SAML_OKTA_AUTH,
            SAML_OKTA_DUO_AUTH, SAML_OKTA_YUBICO_AUTH, SAML_ONELOGIN_AUTH,
            SAML_ONELOGIN_DUO_AUTH, SAML_ONELOGIN_YUBICO_AUTH):
        return flask.abort(405)

    remote_addr = utils.get_remote_addr()
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
    if not utils.const_compare(sig, test_sig):
        journal.entry(
            journal.SSO_AUTH_FAILURE,
            state=state,
            remote_address=remote_addr,
            reason=journal.SSO_AUTH_REASON_INVALID_CALLBACK,
            reason_long='Signature mismatch',
        )
        return flask.abort(401)

    params = urlparse.parse_qs(query)

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
            org_names = [x for x in org_names if x]
        org_names = sorted(org_names)

        groups = []
        if params.get('groups'):
            groups_param = params.get('groups')[0]
            if ';' in groups_param:
                groups = groups_param.split(';')
            else:
                groups = groups_param.split(',')
            groups = [x for x in groups if x]
        groups = set(groups)

        if not username:
            return flask.abort(406)

        org_id = settings.app.sso_org
        if org_names:
            not_found = False
            for org_name in org_names:
                org = organization.get_by_name(
                    utils.filter_unicode(org_name),
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
                utils.filter_unicode(org_name),
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
                    utils.filter_unicode(org_name),
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
                    utils.filter_unicode(org_name),
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
                    utils.filter_unicode(org_name),
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
        token = utils.generate_secret()

        tokens_collection = mongo.get_collection('sso_tokens')
        tokens_collection.insert({
            '_id': token,
            'type': DUO_AUTH,
            'username': username,
            'email': email,
            'org_id': org_id,
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

        duo_page.data = duo_page.data.replace('<%= body_class %>', body_class)
        duo_page.data = duo_page.data.replace('<%= token %>', token)
        duo_page.data = duo_page.data.replace('<%= duo_mode %>', duo_mode)

        return duo_page.get_response()

    if YUBICO_AUTH in sso_mode:
        token = utils.generate_secret()

        tokens_collection = mongo.get_collection('sso_tokens')
        tokens_collection.insert({
            '_id': token,
            'type': YUBICO_AUTH,
            'username': username,
            'email': email,
            'org_id': org_id,
            'groups': list(groups) if groups else None,
            'timestamp': utils.now(),
        })

        yubico_page = static.StaticFile(settings.conf.www_path,
            'yubico.html', cache=False, gzip=False)

        if settings.app.theme == 'dark':
            yubico_page.data = yubico_page.data.replace(
                '<body>', '<body class="dark">')
        yubico_page.data = yubico_page.data.replace('<%= token %>', token)

        return yubico_page.get_response()

    return _validate_user(username, email, sso_mode, org_id, groups,
        remote_addr, http_redirect=True)

@app.app.route('/sso/duo', methods=['POST'])
@auth.open_auth
def sso_duo_post():
    remote_addr = utils.get_remote_addr()
    sso_mode = settings.app.sso
    token = utils.filter_str(flask.request.json.get('token')) or None
    passcode = utils.filter_str(flask.request.json.get('passcode')) or ''

    if sso_mode not in (DUO_AUTH, AZURE_DUO_AUTH, GOOGLE_DUO_AUTH,
            SLACK_DUO_AUTH, SAML_DUO_AUTH, SAML_OKTA_DUO_AUTH,
            SAML_ONELOGIN_DUO_AUTH, RADIUS_DUO_AUTH):
        return flask.abort(404)

    if not token:
        return utils.jsonify({
            'error': TOKEN_INVALID,
            'error_msg': TOKEN_INVALID_MSG,
        }, 401)

    tokens_collection = mongo.get_collection('sso_tokens')
    doc = tokens_collection.find_and_modify(query={
        '_id': token,
    }, remove=True)
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

    return _validate_user(username, email, sso_mode, org_id, groups,
        remote_addr)

@app.app.route('/sso/yubico', methods=['POST'])
@auth.open_auth
def sso_yubico_post():
    remote_addr = utils.get_remote_addr()
    sso_mode = settings.app.sso
    token = utils.filter_str(flask.request.json.get('token')) or None
    key = utils.filter_str(flask.request.json.get('key')) or None

    if sso_mode not in (AZURE_YUBICO_AUTH, GOOGLE_YUBICO_AUTH,
            AUTHZERO_YUBICO_AUTH, SLACK_YUBICO_AUTH, SAML_YUBICO_AUTH,
            SAML_OKTA_YUBICO_AUTH, SAML_ONELOGIN_YUBICO_AUTH):
        return flask.abort(404)

    if not token or not key:
        return utils.jsonify({
            'error': TOKEN_INVALID,
            'error_msg': TOKEN_INVALID_MSG,
        }, 401)

    tokens_collection = mongo.get_collection('sso_tokens')
    doc = tokens_collection.find_and_modify(query={
        '_id': token,
    }, remove=True)
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

    return _validate_user(username, email, sso_mode, org_id, groups,
        remote_addr, yubico_id=yubico_id)
