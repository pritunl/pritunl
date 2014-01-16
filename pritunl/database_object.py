from constants import *
from database import Session
from sqlalchemy import desc

class DatabaseObject:
    def add(self):
        session = Session()
        session.add(self)
        session.commit()

    @classmethod
    def get_rows(cls, sort_column=None, sort_desc=False):
        session = Session()
        if sort_column:
            if sort_desc:
                rows = session.query(cls).order_by(
                    getattr(cls, sort_column).desc())
            else:
                rows = session.query(cls).order_by(getattr(cls, sort_column))
        else:
            rows = session.query(cls).all()
        session.close()
        return rows
