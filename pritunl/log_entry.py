from constants import *
from event import Event
from database import Base, Session
import time
import uuid
from sqlalchemy import Column, Integer, String

class LogEntry(Base):
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
            session = Session()
            session.add(self)
            session.commit()
            Event(type=LOG_UPDATED)
        else:
            self.id = id

    @classmethod
    def get_log_entries(cls):
        log_entries = []
        session = Session()
        log_entries_query = session.query(cls).order_by(
            getattr(cls, 'time').desc())
        for log_entry in log_entries_query:
            if len(log_entries) >= LOG_LIMIT:
                session.delete(log_entry)
                continue
            log_entries.append(log_entry)
        session.commit()
        return log_entries
