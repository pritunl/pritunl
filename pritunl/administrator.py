from constants import *
from exceptions import *
from mongo_object import MongoObject
from cache import cache_db
import utils
import mongo
import base64
import os
import re
import hashlib
import flask
import time
import datetime
import hmac

class Administrator(MongoObject):
    fields = {
        'username',
        'password',
        'token',
        'secret',
        'default',
    }

    def __init__(self, username=None, password=None, default=None, **kwargs):
        MongoObject.__init__(self, **kwargs)

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

    @staticmethod
    def get_nonces_collection():
        return mongo.get_collection('auth_nonces')

    def _hash_password(self, salt, password):
        pass_hash = hashlib.sha512()
        pass_hash.update(password[:PASSWORD_LEN_LIMIT])
        pass_hash.update(base64.b64decode(salt))
        hash_digest = pass_hash.digest()

        for i in xrange(10):
            pass_hash = hashlib.sha512()
            pass_hash.update(hash_digest)
            hash_digest = pass_hash.digest()
        return hash_digest

    def test_password(self, test_pass):
        pass_ver, pass_salt, pass_hash = self.password.split('$')
        test_hash = base64.b64encode(self._hash_password(pass_salt, test_pass))
        return pass_hash == test_hash

    def generate_token(self):
        self.token = re.sub(r'[\W_]+', '',
            base64.b64encode(os.urandom(64)))[:32]

    def generate_secret(self):
        self.secret = re.sub(r'[\W_]+', '',
            base64.b64encode(os.urandom(64)))[:32]

    def commit(self, *args, **kwargs):
        if 'password' in self.changed:
            salt = base64.b64encode(os.urandom(8))
            pass_hash = base64.b64encode(
                self._hash_password(salt, self.password))
            pass_hash = '1$%s$%s' % (salt, pass_hash)
            self.password = pass_hash

            if self.default and self.exists:
                self.default = None

        if not self.token :
            self.generate_token()
        if not self.secret:
            self.generate_secret()

        MongoObject.commit(self, *args, **kwargs)

    @staticmethod
    def get_collection():
        return mongo.get_collection('administrators')

    @classmethod
    def get_user(cls, id):
        return cls(id=id)

    @classmethod
    def find_user(cls, username=None, token=None):
        spec = {}

        if username is not None:
            spec['username'] = username
        if token is not None:
            spec['token'] = token

        return cls(spec=spec)

    @classmethod
    def check_session(cls):
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
                        AUTH_TIME_WINDOW:
                    return False
            except ValueError:
                return False

            administrator = cls.find_user(token=auth_token)
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

            cls.get_nonces_collection().insert({
                'token': auth_token,
                'nonce': auth_nonce,
                'timestamp': datetime.datetime.utcnow(),
            })

            flask.request.administrator = administrator
        else:
            from pritunl import app_server
            if not flask.session:
                return False

            admin_id = flask.session.get('admin_id')
            if not admin_id:
                return False

            administrator = cls.get_user(id=admin_id)
            if not administrator:
                return False

            if not app_server.ssl and flask.session.get(
                    'source') != utils.get_remote_addr():
                flask.session.clear()
                return False

            if SESSION_TIMEOUT and int(time.time()) - \
                    flask.session['timestamp'] > SESSION_TIMEOUT:
                flask.session.clear()
                return False

            flask.request.administrator = administrator
        return True

    @classmethod
    def check_auth(cls, username, password, remote_addr=None):
        if remote_addr:
            # TODO
            cache_key = 'ip_' + remote_addr
            count = cache_db.list_length(cache_key)
            if count and count > 10:
                raise flask.abort(403)

            # TODO
            key_exists = cache_db.exists(cache_key)
            cache_db.list_rpush(cache_key, '')
            if not key_exists:
                cache_db.expire(cache_key, 20)

        administrator = cls.find_user(username=username)
        if not administrator:
            return
        if not administrator.test_password(password):
            return
        return administrator
