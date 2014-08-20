from constants import *
from exceptions import *
from mongo_object import MongoObject
import mongo
import base64
import os
import re
import hashlib

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
