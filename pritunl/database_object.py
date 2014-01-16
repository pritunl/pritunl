from constants import *
from database import Session
from sqlalchemy import desc

class DatabaseObject:
    def add(self):
        session = Session()
        session.add(self)
        session.commit()
