from constants import *
from pritunl import app_server
import logging

logger = logging.getLogger(APP_NAME)
_RESERVED_ATTRIBUTES = ['column_family', 'bool_columns', 'int_columns',
    'float_columns', 'str_columns', 'cached_columns', 'required_columns',
    'all_columns', 'id']

class DatabaseObject:
    db = app_server.app_db
    column_family = 'column_family'
    bool_columns = []
    int_columns = []
    float_columns = []
    str_columns = []
    cached_columns = []
    required_columns = []

    def __init__(self):
        self.all_columns = self.bool_columns + self.int_columns + \
            self.float_columns + self.str_columns
        self.id = None

    def __setattr__(self, name, value):
        if name not in _RESERVED_ATTRIBUTES and name in self.all_columns:
            if name in self.cached_columns:
                self.__dict__[name] = value

            if name in self.int_columns or name in self.float_columns:
                self.db.set(self.column_family,
                    self.id, name, str(value))
            elif name in self.bool_columns:
                self.db.set(self.column_family,
                    self.id, name, 't' if value else 'f')
            else:
                self.db.set(self.column_family,
                    self.id, name, value)
        else:
            self.__dict__[name] = value

    def __getattr__(self, name):
        if name in _RESERVED_ATTRIBUTES:
            pass
        elif name in self.all_columns and self.id:
            if name in self.cached_columns and name in self.__dict__:
                return self.__dict__[name]

            value = self.db.get(self.column_family, self.id, name)

            if name in self.int_columns:
                if value:
                    value = int(value)
            elif name in self.float_columns:
                if value:
                    value = float(value)
            elif name in self.bool_columns:
                if value == 't':
                    value = True
                elif value == 'f':
                    value = False

            if name in self.cached_columns:
                self.__dict__[name] = value

            return value
        elif name in self.cached_columns or name not in self.__dict__:
            raise AttributeError('Object instance has no attribute %r' % name)

        return self.__dict__[name]

    @staticmethod
    def validate(db_obj, row, columns):
        valid = True

        for column in db_obj.required_columns:
            if column not in columns:
                valid = False
                break

            if column in db_obj.int_columns:
                try:
                    int(columns[column])
                except ValueError:
                    valid = False
                    break

        if valid:
            if 'remove' in columns:
                logger.debug('Prevented removal of partially complete' + \
                    ' %s. %r' % (db_obj.column_family, {
                        'event_id': row,
                    }))
                db_obj.db.remove(db_obj.column_family, row, 'remove')
        else:
            # Remove broken rows
            if 'remove' in columns:
                logger.info(('Removing broken %s from ' + \
                    'database. %r') % (db_obj.column_family, {
                        '%s_id' % db_obj.column_family: row,
                    }))
                db_obj.db.remove(db_obj.column_family, row)
            else:
                logger.debug(('Queueing removal of broken %s from' + \
                    ' database. %r') % (db_obj.column_family, {
                        '%s_id' % db_obj.column_family: row,
                    }))
                # Its possible row is currently being created and will
                # be valid once created. Wait for next db clean to
                # revalidate and remove row.
                db_obj.db.set(db_obj.column_family, row, 'remove', 'true')

        return valid
