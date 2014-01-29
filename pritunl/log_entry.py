from constants import *
from cache import persist_db
from event import Event
from cache_object import CacheObject
import time
import uuid

class LogEntry(CacheObject):
    column_family = 'log_entries'
    str_columns = {'type', 'message'}
    int_columns = {'time'}
    cached_columns = {'type', 'message', 'time'}
    db_instance = persist_db

    def __init__(self, id=None, type=None, message=None):
        CacheObject.__init__(self)

        if id is None:
            self.transaction_start()
            self.id = uuid.uuid4().hex
            self.type = type or INFO
            self.time = int(time.time())
            self.message = message
            self.initialize()
            self.transaction_commit()
        else:
            self.id = id

    def dict(self):
        return {
            'id': self.id,
            'time': self.time,
            'message': self.message,
        }

    def initialize(self):
        while self.db.list_length(self.column_family) >= LOG_LIMIT:
            log_entry_id = self.db.list_index(self.column_family, -1)
            if not log_entry_id:
                break
            LogEntry(id=log_entry_id).remove()
        self.db.list_lpush(self.column_family, self.id)
        Event(type=LOG_UPDATED)

    def remove(self):
        self.transaction_start()
        CacheObject.remove(self)
        self.transaction_commit()

    def cache(self):
        self.id = log_entry.id
        self.type = log_entry.type
        self.time = log_entry.time
        self.message = log_entry.message

    @classmethod
    def iter_log_entries(cls):
        for log_entry_id in cls.db_instance.list_iter('log_entries'):
            yield cls(id=log_entry_id)
