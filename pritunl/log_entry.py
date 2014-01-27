from constants import *
from event import Event
from cache_object import CacheObject
from database import Base, Session, db_lock
from cache import cache_db
import time
import uuid
from sqlalchemy import Column, Integer, String

class LogEntrySQL(Base):
    __tablename__ = 'log_entries'
    id = Column(String, primary_key=True)
    type = Column(String)
    time = Column(Integer)
    message = Column(String)

    def __init__(self, id=None, type=None, message=None):
        if id is None:
            self.id = uuid.uuid4().hex
            self.type = type or INFO
            self.time = int(time.time())
            self.message = message
        else:
            self.id = id

    @classmethod
    def iter_log_entries(cls):
        session = Session()
        for log_entry in session.query(cls).order_by(
                getattr(cls, 'time').desc()):
            yield log_entry

class LogEntry(CacheObject):
    column_family = 'log_entries'
    str_columns = {'type', 'message'}
    int_columns = {'time'}
    cached_columns = {'type', 'message', 'time'}

    def __init__(self, id=None, type=None, message=None, sql_object=None):
        CacheObject.__init__(self)

        if sql_object is not None:
            self.id = sql_object.id
            self.type = sql_object.type
            self.time = sql_object.time
            self.message = sql_object.message
        elif id is None:
            log_entry_sql = LogEntrySQL(type=type, message=message)
            self.id = log_entry_sql.id
            self.type = type
            self.time = log_entry_sql.time
            self.message = message
            self.initialize(log_entry_sql)
        else:
            self.id = id

    def dict(self):
        return {
            'id': self.id,
            'time': self.time,
            'message': self.message,
        }

    def initialize(self, log_entry_sql):
        db_lock.acquire()
        try:
            session = Session()
            while cache_db.list_length(self.column_family) >= LOG_LIMIT:
                log_entry_id = cache_db.list_index(self.column_family, -1)
                LogEntry(id=log_entry_id).remove(session)
            session.add(log_entry_sql)
            cache_db.list_lpush(self.column_family, self.id)
            session.commit()
        finally:
            db_lock.release()
        Event(type=LOG_UPDATED)

    def remove(self, session):
        session.delete(session.query(LogEntrySQL).get(self.id))
        CacheObject.remove(self)

    def cache(self):
        self.id = log_entry.id
        self.type = log_entry.type
        self.time = log_entry.time
        self.message = log_entry.message

    @classmethod
    def iter_log_entries(cls):
        if cache_db.get('log_entries_cached') != 't':
            cache_db.remove('log_entries')
            for sql_log_entry in LogEntrySQL.iter_log_entries():
                log_entry = cls(sql_object=sql_log_entry)
                cache_db.list_rpush('log_entries', log_entry.id)
                yield log_entry
            cache_db.set('log_entries_cached', 't')
            return

        for log_entry_id in cache_db.list_iter('log_entries'):
            yield cls(id=log_entry_id)
