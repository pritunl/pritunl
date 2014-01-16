from constants import *
import threading
import logging
import copy
import urlparse
import time
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import StaticPool

logger = logging.getLogger(APP_NAME)

Session = sessionmaker()
Base = declarative_base()

def connect_database(sql_connection):
    from log_entry import LogEntry
    engine = create_engine(sql_connection)
    Session.configure(bind=engine)
    engineConn = engine.connect()
    Base.metadata.create_all(engine)
