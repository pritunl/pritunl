from constants import *
from cache_object import CacheObject
import time
import uuid

class AuthToken(CacheObject):
    column_family = 'auth_tokens'
    int_columns = {'time'}
    cached_columns = {'time'}

    def __init__(self, id=None):
        CacheObject.__init__(self)

        if id is None:
            self.id = uuid.uuid4().hex
            self.time = int(time.time())
            self.initialize()
        else:
            self.id = id

    def __getattr__(self, name):
        if name == 'valid':
            return bool(self.time)
        return CacheObject.__getattr__(self, name)
