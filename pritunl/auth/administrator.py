from pritunl.auth.utils import *
from pritunl.auth.csrf import validate_token

from pritunl.constants import *
from pritunl.helpers import *
from pritunl import settings
from pritunl import utils
from pritunl import mongo
from pritunl import logger
from pritunl import journal
from pritunl import plugins
from pritunl import sso

import base64
import os
import hashlib
import flask
import datetime
import hmac
import pymongo
import struct

class Administrator(mongo.MongoObject):
    fields = {
        'username',
        'password',
        'default_password',
        'yubikey_id',
        'otp_auth',
        'otp_secret',
        'auth_api',
        'token',
        'secret',
        'default',
        'disabled',
        'sessions',
        'super_user',
    }
    fields_default = {
        'super_user': True,
        'sessions': [],
    }

    def __init__(self, username=None, password=None, default=None,
            yubikey_id=None, otp_auth=None, auth_api=None, disabled=None,
            super_user=None, **kwargs):
        mongo.MongoObject.__init__(self)
        if username is not None:
            self.username = username
        if password is not None:
            self.password = password
        if default is not None:
            self.default = default
        if yubikey_id is not None:
            self.yubikey_id = yubikey_id
        if otp_auth is not None:
            self.otp_auth = otp_auth
        if auth_api is not None:
            self.auth_api = auth_api
        if disabled is not None:
            self.disabled = disabled
        if super_user is not None:
            self.super_user = super_user

    def dict(self):
        if settings.app.demo_mode:
            return {
                'id': self.id,
                'username': self.username,
                'yubikey_id': 'demo',
                'otp_auth': self.otp_auth,
                'otp_secret': self.otp_secret,
                'auth_api': self.auth_api,
                'token': 'demo',
                'secret': 'demo',
                'default': self.default,
                'disabled': self.disabled,
                'super_user': self.super_user,
            }
        return {
            'id': self.id,
            'username': self.username,
            'yubikey_id': self.yubikey_id,
            'otp_auth': self.otp_auth,
            'otp_secret': self.otp_secret,
            'auth_api': self.auth_api,
            'token': self.token,
            'secret': self.secret,
            'default': self.default,
            'disabled': self.disabled,
            'super_user': self.super_user,
        }

    @property
    def journal_data(self):
        return {
            'admin_id': self.id,
            'admin_name': self.username,
            'admin_super_user': self.super_user,
        }

    @cached_static_property
    def collection(cls):
        return mongo.get_collection('administrators')

    @cached_static_property
    def audit_collection(cls):
        return mongo.get_collection('users_audit')

    @cached_static_property
    def nonces_collection(cls):
        return mongo.get_collection('auth_nonces')

    @cached_static_property
    def limiter_collection(cls):
        return mongo.get_collection('auth_limiter')

    @cached_static_property
    def otp_collection(cls):
        return mongo.get_collection('otp')

    def test_password(self, test_pass):
        hash_ver, pass_salt, pass_hash = self.password.split('$')

        if not test_pass:
            return False

        if hash_ver == '0':
            hash_func = hash_password_v0
        elif hash_ver == '1':
            hash_func = hash_password_v1
        elif hash_ver == '2':
            hash_func = hash_password_v2
        elif hash_ver == '3':
            hash_func = hash_password_v3
        else:
            raise ValueError('Unknown hash version')

        test_hash = base64.b64encode(hash_func(pass_salt, test_pass)).decode()
        return utils.const_compare(pass_hash, test_hash)

    def auth_check(self, password, otp_code=None, yubico_key=None,
            remote_addr=None):
        if not self.test_password(password):
            journal.entry(
                journal.ADMIN_AUTH_FAILURE,
                self.journal_data,
                remote_address=remote_addr,
                reason=journal.ADMIN_AUTH_REASON_INVALID_PASSWORD,
                reason_long='Invalid password',
            )

            self.audit_event(
                'admin_auth',
                'Administrator login failed, invalid password',
                remote_addr=remote_addr,
            )
            return False

        if self.otp_auth and not self.verify_otp_code(otp_code):
            journal.entry(
                journal.ADMIN_AUTH_FAILURE,
                self.journal_data,
                remote_address=remote_addr,
                reason=journal.ADMIN_AUTH_REASON_INVALID_OTP,
                reason_long='Invalid two-factor authentication code',
            )

            self.audit_event(
                'admin_auth',
                'Administrator login failed, ' +
                    'invalid two-factor authentication code',
                remote_addr=remote_addr,
            )
            return False

        if self.yubikey_id:
            valid, public_id = sso.auth_yubico(yubico_key)
            if not valid or self.yubikey_id != public_id:
                journal.entry(
                    journal.ADMIN_AUTH_FAILURE,
                    self.journal_data,
                    remote_address=remote_addr,
                    reason=journal.ADMIN_AUTH_REASON_INVALID_YUBIKEY,
                    reason_long='Invalid YubiKey',
                )

                self.audit_event(
                    'admin_auth',
                    'Administrator login failed, invalid YubiKey',
                    remote_addr=remote_addr,
                )
                return False

        if self.disabled:
            journal.entry(
                journal.ADMIN_AUTH_FAILURE,
                self.journal_data,
                remote_address=remote_addr,
                reason=journal.ADMIN_AUTH_REASON_DISABLED,
                reason_long='Account is disabled',
            )

            self.audit_event(
                'admin_auth',
                'Administrator login failed, administrator is disabled',
                remote_addr=remote_addr,
            )
            return False

        journal.entry(
            journal.ADMIN_AUTH_SUCCESS,
            self.journal_data,
            remote_address=remote_addr,
        )

        self.audit_event(
            'admin_auth',
            'Administrator login successful',
            remote_addr=remote_addr,
        )

        return True

    def generate_otp_secret(self):
        self.otp_secret = utils.generate_otp_secret()

    def verify_otp_code(self, code):
        otp_secret = self.otp_secret
        padding = 8 - len(otp_secret) % 8
        if padding != 8:
            otp_secret = otp_secret.ljust(len(otp_secret) + padding, '=')
        otp_secret = base64.b32decode(otp_secret.upper())
        valid_codes = []
        epoch = int(utils.time_now() / 30)
        for epoch_offset in range(-1, 2):
            value = struct.pack('>q', epoch + epoch_offset)
            hmac_hash = hmac.new(otp_secret, value, hashlib.sha1).digest()
            offset = hmac_hash[-1] & 0x0F
            truncated_hash = hmac_hash[offset:offset + 4]
            truncated_hash = struct.unpack('>L', truncated_hash)[0]
            truncated_hash &= 0x7FFFFFFF
            truncated_hash %= 1000000
            valid_codes.append('%06d' % truncated_hash)

        if code not in valid_codes:
            return False

        response = self.otp_collection.update({
            '_id': {
                'user_id': self.id,
                'code': code,
            },
        }, {'$set': {
            'timestamp': utils.now(),
        }}, upsert=True)

        if response['updatedExisting']:
            return False

        return True

    def generate_token(self):
        self.token = utils.generate_secret()

    def generate_secret(self):
        self.secret = utils.generate_secret()

    def generate_default_password(self):
        password = utils.rand_str(12)
        self.password = password
        self.default_password = password
        self.default = True

    def new_session(self):
        session_id = utils.generate_secret()
        self.collection.update({
            '_id': self.id,
        }, {'$push': {
            'sessions': {
                '$each': [session_id],
                '$slice': -settings.app.session_limit,
            },
        }})
        return session_id

    def commit(self, *args, **kwargs):
        if 'password' in self.changed:
            if not self.password:
                raise ValueError('Password is empty')

            salt = base64.b64encode(os.urandom(8))
            pass_hash = base64.b64encode(
                hash_password_v3(salt, self.password)).decode()
            pass_hash = '3$%s$%s' % (salt.decode(), pass_hash)
            self.password = pass_hash

            if self.default and self.exists:
                self.default = None
                self.default_password = None

        if not self.token:
            self.generate_token()
        if not self.secret:
            self.generate_secret()

        mongo.MongoObject.commit(self, *args, **kwargs)

    def audit_event(self, event_type, event_msg, remote_addr=None):
        if settings.app.auditing != ALL:
            return

        timestamp = utils.now()

        self.audit_collection.insert({
            'user_id': self.id,
            'timestamp': timestamp,
            'type': event_type,
            'remote_addr': remote_addr,
            'message': event_msg,
        })

        plugins.event(
            'audit_event',
            host_id=settings.local.host_id,
            host_name=settings.local.host.name,
            user_id=self.id,
            org_id=None,
            timestamp=timestamp,
            type=event_type,
            remote_addr=remote_addr,
            message=event_msg,
        )

        logger.info(
            'Administrator audit event',
            'audit',
            user_id=self.id,
            timestamp=timestamp,
            type=event_type,
            remote_addr=remote_addr,
            message=event_msg,
        )

    def get_audit_events(self):
        if settings.app.demo_mode:
            return DEMO_ADMIN_AUDIT_EVENTS

        events = []
        spec = {
            'user_id': self.id,
        }

        for doc in self.audit_collection.find(spec).sort(
                'timestamp', pymongo.DESCENDING).limit(
                settings.user.audit_limit):
            doc['timestamp'] = int(doc['timestamp'].strftime('%s'))
            events.append(doc)

        return events

def clear_session(id, session_id):
    Administrator.collection.update({
        '_id': id,
    }, {'$pull': {
        'sessions': session_id,
    }})

def get_user(id, session_id):
    if not session_id:
        return

    return Administrator(spec={
        '_id': id,
        'sessions': session_id,
    })

def find_user(username=None, token=None):
    spec = {}

    if username is not None:
        spec['username'] = username
    if token is not None:
        spec['token'] = token

    return Administrator(spec=spec)

def check_session(csrf_check):
    auth_token = flask.request.headers.get('Auth-Token', None)
    if auth_token:
        auth_timestamp = flask.request.headers.get('Auth-Timestamp', None)
        auth_nonce = flask.request.headers.get('Auth-Nonce', None)
        auth_signature = flask.request.headers.get('Auth-Signature', None)
        if not auth_token or not auth_timestamp or not auth_nonce or \
                not auth_signature:
            return False
        auth_token = auth_token[:256]
        auth_timestamp = auth_timestamp[:64]
        auth_nonce = auth_nonce[:32]
        auth_signature = auth_signature[:512]

        try:
            if abs(int(auth_timestamp) - int(utils.time_now())) > \
                    settings.app.auth_time_window:
                return False
        except ValueError:
            return False

        administrator = find_user(token=auth_token)
        if not administrator:
            return False

        if not administrator.auth_api:
            return False

        auth_string = '&'.join([
            auth_token, auth_timestamp, auth_nonce, flask.request.method,
            flask.request.path])

        if len(auth_string) > AUTH_SIG_STRING_MAX_LEN or len(auth_nonce) < 8:
            return False

        if not administrator.secret or len(administrator.secret) < 8:
            return False

        auth_test_signature = base64.b64encode(hmac.new(
            administrator.secret.encode(), auth_string.encode(),
            hashlib.sha256).digest())
        if not utils.const_compare(auth_signature, auth_test_signature):
            return False

        try:
            Administrator.nonces_collection.insert({
                'token': auth_token,
                'nonce': auth_nonce,
                'timestamp': utils.now(),
            })
        except pymongo.errors.DuplicateKeyError:
            return False
    else:
        if not flask.session:
            return False

        admin_id = utils.session_opt_str('admin_id')
        if not admin_id:
            return False
        admin_id = utils.ObjectId(admin_id)
        session_id = utils.session_opt_str('session_id')

        signature = utils.session_opt_str('signature')
        if not signature:
            return False

        if not utils.check_flask_sig():
            return False

        if csrf_check:
            csrf_token = flask.request.headers.get('Csrf-Token', None)
            if not validate_token(admin_id, csrf_token):
                return False

        administrator = get_user(admin_id, session_id)
        if not administrator:
            return False

        if not settings.app.reverse_proxy and \
                not settings.app.allow_insecure_session and \
                not settings.app.server_ssl and \
                utils.session_opt_str('source') != utils.get_remote_addr():
            flask.session.clear()
            clear_session(admin_id, session_id)
            return False

        session_timeout = settings.app.session_timeout
        if session_timeout and int(utils.time_now()) - \
                utils.session_int('timestamp') > session_timeout:
            flask.session.clear()
            clear_session(admin_id, session_id)
            return False

        flask.session['timestamp'] = int(utils.time_now())
        utils.set_flask_sig()

    if administrator.disabled:
        return False

    flask.g.administrator = administrator
    return True

def get_default_password():
    logger.info('Getting default administrator password', 'auth')

    time.sleep(0.2)

    default_admin = find_user(username=DEFAULT_USERNAME)
    if not default_admin:
        return None, None

    return default_admin.username, default_admin.default_password

def get_by_username(username):
    username = utils.filter_str(username).lower()

    admin = find_user(username=username)
    if not admin:
        return

    return admin

def reset_password():
    logger.info('Resetting administrator password', 'auth')

    time.sleep(0.2)

    admin_collection = mongo.get_collection('administrators')

    response = admin_collection.delete_one({
        'username': 'pritunl',
    })
    if not response.deleted_count:
        admin_collection.delete_one({
            'super_user': {'$ne': False},
        })

    default_admin = Administrator(
        username=DEFAULT_USERNAME,
    )
    default_admin.generate_default_password()
    default_admin.commit()

    return DEFAULT_USERNAME, default_admin.default_password

def iter_admins(fields=None):
    if fields:
        fields = {key: True for key in fields}

    cursor = Administrator.collection.find({}, fields).sort('name')

    for doc in cursor:
        yield Administrator(doc=doc, fields=fields)

def get_by_id(id, fields=None):
    return Administrator(id=id, fields=fields)

def new_admin(**kwargs):
    admin = Administrator(**kwargs)

    if admin.otp_auth:
        admin.generate_otp_secret()

    if admin.auth_api:
        admin.generate_token()
        admin.generate_secret()

    admin.commit()

    return admin

def super_user_count():
    return Administrator.collection.find({
        'super_user': {'$ne': False},
        'disabled': {'$ne': True},
    }, {
        '_id': True,
    }).count()

has_default_pass = None
def has_default_password():
    global has_default_pass

    if has_default_pass is None or has_default_pass:
        default_admin = find_user(username=DEFAULT_USERNAME)
        if not default_admin:
            has_default_pass = False
            return has_default_pass

        has_default_pass = bool(default_admin.default_password)
        return has_default_pass
    return False
