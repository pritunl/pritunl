from pritunl.constants import *
from pritunl import utils
from pritunl import event
from pritunl import app
from pritunl import auth
from pritunl import settings
from pritunl import journal

import flask
import pymongo

@app.app.route('/admin', methods=['GET'])
@app.app.route('/admin/<admin_id>', methods=['GET'])
@auth.session_auth
def admin_get(admin_id=None):
    if settings.app.demo_mode:
        resp = utils.demo_get_cache()
        if resp:
            return utils.jsonify(resp)

    if not flask.g.administrator.super_user:
        return utils.jsonify({
            'error': REQUIRES_SUPER_USER,
            'error_msg': REQUIRES_SUPER_USER_MSG,
        }, 400)

    if admin_id:
        return utils.jsonify(auth.get_by_id(admin_id).dict())

    admins = []

    for admin in auth.iter_admins():
        admin = admin.dict()
        admin['audit'] = settings.app.auditing == ALL
        admins.append(admin)

    if settings.app.demo_mode:
        utils.demo_set_cache(admins)
    return utils.jsonify(admins)

@app.app.route('/admin/<admin_id>', methods=['PUT'])
@auth.session_auth
def admin_put(admin_id):
    if settings.app.demo_mode:
        return utils.demo_blocked()

    if not flask.g.administrator.super_user:
        return utils.jsonify({
            'error': REQUIRES_SUPER_USER,
            'error_msg': REQUIRES_SUPER_USER_MSG,
        }, 400)

    admin = auth.get_by_id(admin_id)
    remote_addr = utils.get_remote_addr()

    if 'username' in flask.request.json:
        username = utils.filter_str(flask.request.json['username']) or \
            'undefined'
        if username:
            username = username.lower()

        if username != admin.username:
            admin.audit_event('admin_updated',
                'Administrator username changed',
                remote_addr=remote_addr,
            )

            journal.entry(
                journal.ADMIN_UPDATE,
                admin.journal_data,
                event_long='Administrator username changed',
                remote_addr=remote_addr,
            )

        admin.username = username

    if 'password' in flask.request.json and flask.request.json['password']:
        password = flask.request.json['password']

        if password != admin.password:
            admin.audit_event('admin_updated',
                'Administrator password changed',
                remote_addr=remote_addr,
            )

            journal.entry(
                journal.ADMIN_UPDATE,
                admin.journal_data,
                event_long='Administrator password changed',
                remote_addr=remote_addr,
            )

        admin.password = password

    if 'yubikey_id' in flask.request.json:
        yubikey_id = flask.request.json['yubikey_id'] or None

        if yubikey_id != admin.yubikey_id:
            admin.audit_event('admin_updated',
                'Administrator YubiKey ID changed',
                remote_addr=remote_addr,
            )

            journal.entry(
                journal.ADMIN_UPDATE,
                admin.journal_data,
                event_long='Administrator YubiKey ID changed',
                remote_addr=remote_addr,
            )

        admin.yubikey_id = yubikey_id[:12] if yubikey_id else None

    super_user = flask.request.json.get('super_user')
    if super_user is not None:
        if super_user != admin.super_user:
            if not super_user and auth.super_user_count() < 2:
                return utils.jsonify({
                    'error': NO_SUPER_USERS,
                    'error_msg': NO_SUPER_USERS_MSG,
                }, 400)

            admin.audit_event('admin_updated',
                'Administrator super user %s' % (
                    'disabled' if super_user else 'enabled'),
                remote_addr=remote_addr,
            )

            journal.entry(
                journal.ADMIN_UPDATE,
                admin.journal_data,
                event_long='Administrator super user %s' % (
                    'disabled' if super_user else 'enabled'),
                remote_addr=remote_addr,
            )

        admin.super_user = super_user

    auth_api = flask.request.json.get('auth_api')
    if auth_api is not None:
        if auth_api != admin.auth_api:
            if not auth_api:
                admin.token = None
                admin.secret = None
            elif not admin.token or not admin.secret:
                admin.generate_token()
                admin.generate_secret()

            admin.audit_event('admin_updated',
                'Administrator token authentication %s' % (
                    'disabled' if auth_api else 'enabled'),
                remote_addr=remote_addr,
            )

            journal.entry(
                journal.ADMIN_UPDATE,
                admin.journal_data,
                event_long='Administrator token authentication %s' % (
                    'disabled' if auth_api else 'enabled'),
                remote_addr=remote_addr,
            )

        admin.auth_api = auth_api

    if 'token' in flask.request.json and flask.request.json['token']:
        admin.generate_token()
        admin.audit_event('admin_updated',
            'Administrator api token changed',
            remote_addr=remote_addr,
        )

        journal.entry(
            journal.ADMIN_UPDATE,
            admin.journal_data,
            event_long='Administrator api token changed',
            remote_addr=remote_addr,
        )

    if 'secret' in flask.request.json and flask.request.json['secret']:
        admin.generate_secret()
        admin.audit_event('admin_updated',
            'Administrator api secret changed',
            remote_addr=remote_addr,
        )

        journal.entry(
            journal.ADMIN_UPDATE,
            admin.journal_data,
            event_long='Administrator api secret changed',
            remote_addr=remote_addr,
        )

    disabled = flask.request.json.get('disabled')
    if disabled is not None:
        if disabled != admin.disabled:
            if disabled and admin.super_user and auth.super_user_count() < 2:
                return utils.jsonify({
                    'error': NO_ADMINS_ENABLED,
                    'error_msg': NO_ADMINS_ENABLED_MSG,
                }, 400)

            admin.audit_event('admin_updated',
                'Administrator %s' % ('disabled' if disabled else 'enabled'),
                remote_addr=remote_addr,
            )

            journal.entry(
                journal.ADMIN_UPDATE,
                admin.journal_data,
                event_long='Administrator %s' % (
                    'disabled' if disabled else 'enabled'),
                remote_addr=remote_addr,
            )

        admin.disabled = disabled

    otp_auth = flask.request.json.get('otp_auth')
    if otp_auth is not None:
        if otp_auth != admin.otp_auth:
            if not otp_auth:
                admin.otp_secret = None
            elif not admin.otp_secret:
                admin.generate_otp_secret()

            admin.audit_event('admin_updated',
                'Administrator two-step authentication %s' % (
                    'disabled' if otp_auth else 'enabled'),
                remote_addr=remote_addr,
            )

            journal.entry(
                journal.ADMIN_UPDATE,
                admin.journal_data,
                event_long='Administrator two-step authentication %s' % (
                    'disabled' if otp_auth else 'enabled'),
                remote_addr=remote_addr,
            )

        admin.otp_auth = otp_auth

    otp_secret = flask.request.json.get('otp_secret')
    if otp_secret == True:
        admin.audit_event('admin_updated',
            'Administrator two-factor authentication secret reset',
            remote_addr=remote_addr,
        )

        journal.entry(
            journal.ADMIN_UPDATE,
            admin.journal_data,
            event_long='Administrator two-factor authentication secret reset',
            remote_addr=remote_addr,
        )
        admin.generate_otp_secret()

    try:
        admin.commit()
    except pymongo.errors.DuplicateKeyError:
        return utils.jsonify({
            'error': ADMIN_USERNAME_EXISTS,
            'error_msg': ADMIN_USERNAME_EXISTS_MSG,
        }, 400)

    event.Event(type=ADMINS_UPDATED)

    return utils.jsonify(admin.dict())

@app.app.route('/admin', methods=['POST'])
@auth.session_auth
def admin_post():
    if settings.app.demo_mode:
        return utils.demo_blocked()

    if not flask.g.administrator.super_user:
        return utils.jsonify({
            'error': REQUIRES_SUPER_USER,
            'error_msg': REQUIRES_SUPER_USER_MSG,
        }, 400)

    username = utils.filter_str(flask.request.json['username']).lower()
    password = flask.request.json['password']
    yubikey_id = flask.request.json.get('yubikey_id') or None
    yubikey_id = yubikey_id[:12] if yubikey_id else None
    otp_auth = flask.request.json.get('otp_auth', False)
    auth_api = flask.request.json.get('auth_api', False)
    disabled = flask.request.json.get('disabled', False)
    super_user = flask.request.json.get('super_user', False)
    remote_addr = utils.get_remote_addr()

    try:
        admin = auth.new_admin(
            username=username,
            password=password,
            yubikey_id=yubikey_id,
            default=True,
            otp_auth=otp_auth,
            auth_api=auth_api,
            disabled=disabled,
            super_user=super_user,
        )
    except pymongo.errors.DuplicateKeyError:
        return utils.jsonify({
            'error': ADMIN_USERNAME_EXISTS,
            'error_msg': ADMIN_USERNAME_EXISTS_MSG,
        }, 400)

    admin.audit_event('admin_created',
        'Administrator created',
        remote_addr=remote_addr,
    )

    journal.entry(
        journal.ADMIN_CREATE,
        admin.journal_data,
        event_long='Administrator created',
        remote_addr=remote_addr,
    )

    event.Event(type=ADMINS_UPDATED)

    return utils.jsonify(admin.dict())

@app.app.route('/admin/<admin_id>', methods=['DELETE'])
@auth.session_auth
def admin_delete(admin_id):
    if settings.app.demo_mode:
        return utils.demo_blocked()

    if not flask.g.administrator.super_user:
        return utils.jsonify({
            'error': REQUIRES_SUPER_USER,
            'error_msg': REQUIRES_SUPER_USER_MSG,
        }, 400)

    admin = auth.get_by_id(admin_id)
    remote_addr = utils.get_remote_addr()

    if admin.super_user and auth.super_user_count() < 2:
        return utils.jsonify({
            'error': NO_ADMINS,
            'error_msg': NO_ADMINS_MSG,
        }, 400)

    journal.entry(
        journal.ADMIN_DELETE,
        admin.journal_data,
        event_long='Administrator deleted',
        remote_addr=remote_addr,
    )

    admin.remove()
    event.Event(type=ADMINS_UPDATED)

    return utils.jsonify({})

@app.app.route('/admin/<admin_id>/audit', methods=['GET'])
@auth.session_auth
def admin_audit_get(admin_id):
    if settings.app.demo_mode:
        resp = utils.demo_get_cache()
        if resp:
            return utils.jsonify(resp)

    if not flask.g.administrator.super_user:
        return utils.jsonify({
            'error': REQUIRES_SUPER_USER,
            'error_msg': REQUIRES_SUPER_USER_MSG,
        }, 400)

    admin = auth.get_by_id(admin_id)

    resp = admin.get_audit_events()
    if settings.app.demo_mode:
        utils.demo_set_cache(resp)
    return utils.jsonify(resp)
