from constants import *
from cache_object import CacheObject
import time
import uuid
import base64
import os
import re

class AuthSecret(CacheObject):
    column_family = 'auth_secrets'
    str_columns = {'secret'}
    int_columns = {'time'}
    cached_columns = {'secret', 'time'}

    def __init__(self, id=None):
        CacheObject.__init__(self)

        if id is None:
            self.id = uuid.uuid4().hex
            self.time = int(time.time())
            self.secret = re.sub(r'[\W_]+', '',
                base64.b64encode(os.urandom(64)))[:32]
            self.initialize()
        else:
            self.id = id

    def __getattr__(self, name):
        if name == 'valid':
            return bool(self.time)
        return CacheObject.__getattr__(self, name)
