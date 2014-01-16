from constants import *
from event import Event
from database_object import DatabaseObject
from database import Base
import logging
import time
import uuid
from sqlalchemy import Column, Integer, String

logger = logging.getLogger(APP_NAME)

class LogEntry(Base, DatabaseObject):
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
            self.add()
            Event(type=LOG_UPDATED)
        else:
            self.id = id
