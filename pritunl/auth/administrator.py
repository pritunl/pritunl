from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *
from pritunl import settings
from pritunl import utils
from pritunl import mongo
from pritunl import logger

import base64
import os
import re
import hashlib
import flask
import time
import datetime
import hmac
import pymongo
import bson

class Administrator(mongo.MongoObject):
    fields = {
        'username',
        'password',
        'token',
        'secret',
        'default',
        'sessions',
    }
    fields_default = {
        'sessions': [],
    }

    def __init__(self, username=None, password=None, default=None, **kwargs):
        mongo.MongoObject.__init__(self, **kwargs)

        if username is not None:
            self.username = username
        if password is not None:
            self.password = password
        if default is not None:
            self.default = default

    def dict(self):
        return {
            'username': self.username,
            'token': self.token,
            'secret': self.secret,
            'default': self.default,
        }

    @cached_static_property
    def collection(cls):
        return mongo.get_collection('administrators')

    @cached_static_property
    def nonces_collection(cls):
        return mongo.get_collection('auth_nonces')

    @cached_static_property
    def limiter_collection(cls):
        return mongo.get_collection('auth_limiter')

    def _hash_password(self, salt, password):
        pass_hash = hashlib.sha512()
        pass_hash.update(password[:settings.app.password_len_limit])
        pass_hash.update(base64.b64decode(salt))
        hash_digest = pass_hash.digest()

        for _ in xrange(10):
            pass_hash = hashlib.sha512()
            pass_hash.update(hash_digest)
            hash_digest = pass_hash.digest()
        return hash_digest

    def test_password(self, test_pass):
        _, pass_salt, pass_hash = self.password.split('$')
        test_hash = base64.b64encode(self._hash_password(pass_salt, test_pass))
        return pass_hash == test_hash

    def generate_token(self):
        logger.info('Generating auth token', 'auth')

        self.token = re.sub(r'[\W_]+', '',
            base64.b64encode(os.urandom(64)))[:32]

    def generate_secret(self):
        logger.info('Generating auth secret', 'auth')

        self.secret = re.sub(r'[\W_]+', '',
            base64.b64encode(os.urandom(64)))[:32]

    def commit(self, *args, **kwargs):
        if 'password' in self.changed:
            logger.info('Changing administrator password', 'auth',
                username=self.username,
            )

            salt = base64.b64encode(os.urandom(8))
            pass_hash = base64.b64encode(
                self._hash_password(salt, self.password))
            pass_hash = '1$%s$%s' % (salt, pass_hash)
            self.password = pass_hash

            if self.default and self.exists:
                self.default = None

        if not self.token:
            self.generate_token()
        if not self.secret:
            self.generate_secret()

        mongo.MongoObject.commit(self, *args, **kwargs)

def get_user(id):
    return Administrator(id=id)

def find_user(username=None, token=None):
    spec = {}

    if username is not None:
        spec['username'] = username
    if token is not None:
        spec['token'] = token

    return Administrator(spec=spec)

def check_session():
    auth_token = flask.request.headers.get('Auth-Token', None)
    if auth_token:
        auth_timestamp = flask.request.headers.get('Auth-Timestamp', None)
        auth_nonce = flask.request.headers.get('Auth-Nonce', None)
        auth_signature = flask.request.headers.get('Auth-Signature', None)
        if not auth_token or not auth_timestamp or not auth_nonce or \
                not auth_signature:
            return False
        auth_nonce = auth_nonce[:32]

        try:
            if abs(int(auth_timestamp) - int(time.time())) > \
                    settings.app.auth_time_window:
                return False
        except ValueError:
            return False

        administrator = find_user(token=auth_token)
        if not administrator:
            return False

        auth_string = '&'.join([
            auth_token, auth_timestamp, auth_nonce, flask.request.method,
            flask.request.path] +
            ([flask.request.data] if flask.request.data else []))

        if len(auth_string) > AUTH_SIG_STRING_MAX_LEN:
            return False

        auth_test_signature = base64.b64encode(hmac.new(
            administrator.secret.encode(), auth_string,
            hashlib.sha256).digest())
        if auth_signature != auth_test_signature:
            return False

        try:
            Administrator.nonces_collection.insert({
                'token': auth_token,
                'nonce': auth_nonce,
                'timestamp': utils.now(),
            }, w=0)
        except pymongo.errors.DuplicateKeyError:
            return False
    else:
        if not flask.session:
            return False

        admin_id = flask.session.get('admin_id')
        if not admin_id:
            return False
        admin_id = bson.ObjectId(admin_id)

        administrator = get_user(id=admin_id)
        if not administrator:
            return False

        if not settings.conf.ssl and flask.session.get(
                'source') != utils.get_remote_addr():
            flask.session.clear()
            return False

        session_timeout = settings.app.session_timeout
        if session_timeout and int(time.time()) - \
                flask.session['timestamp'] > session_timeout:
            flask.session.clear()
            return False

        flask.session['timestamp'] = int(time.time())

    flask.g.administrator = administrator
    return True

def check_auth(username, password, remote_addr=None):
    username = utils.filter_str(username).lower()

    if remote_addr:
        doc = Administrator.limiter_collection.find_and_modify({
            '_id': remote_addr,
        }, {
            '$inc': {'count': 1},
            '$setOnInsert': {'timestamp': utils.now()},
        }, new=True, upsert=True)

        if utils.now() > doc['timestamp'] + datetime.timedelta(minutes=1):
            doc = {
                'count': 1,
                'timestamp': utils.now(),
            }
            Administrator.limiter_collection.update({
                '_id': remote_addr,
            }, doc, upsert=True)

        if doc['count'] > settings.app.auth_limiter_count_max:
            raise flask.abort(403)

    administrator = find_user(username=username)
    if not administrator:
        return
    if not administrator.test_password(password):
        return
    return administrator

def reset_password():
    logger.info('Resetting administrator password', 'auth')
    collection = mongo.get_collection('administrators')
    collection.remove({})
    return (DEFAULT_USERNAME, DEFAULT_PASSWORD)
