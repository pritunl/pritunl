from constants import *
from pritunl import app_server
from database_object import DatabaseObject
import logging
import time
import uuid

logger = logging.getLogger(APP_NAME)

class AuthToken(DatabaseObject):
    db = app_server.mem_db
    column_family = 'auth_tokens'
    int_columns = {'time'}
    cached_columns = {'time'}
    required_columns = {'time'}

    def __init__(self, id=None):
        DatabaseObject.__init__(self)

        if id is None:
            self.id = uuid.uuid4().hex
            self.time = int(time.time())
        else:
            self.id = id

    def __getattr__(self, name):
        if name == 'valid':
            return bool(self.time)
        return DatabaseObject.__getattr__(self, name)

    def delete(self):
        self.db.remove(self.column_family, self.id)
