from constants import *
from cache import cache_db

class CacheObject:
    column_family = 'column_family'
    bool_columns = set()
    int_columns = set()
    float_columns = set()
    str_columns = set()
    cached_columns = set()
    db_instance = cache_db

    def __init__(self):
        self.all_columns = self.bool_columns | self.int_columns | \
            self.float_columns | self.str_columns
        self.id = None
        self._trans = None

    def __setattr__(self, name, value):
        if name != 'all_columns' and name in self.all_columns:
            if name in self.cached_columns:
                self.__dict__[name] = value

            if name in self.int_columns or name in self.float_columns:
                value = str(value)
            elif name in self.bool_columns:
                value = 't' if value else 'f'

            self.db.dict_set(self.get_cache_key(), name, value)
        else:
            self.__dict__[name] = value

    def __getattr__(self, name):
        if name in self.all_columns and self.id:
            if name in self.cached_columns and name in self.__dict__:
                return self.__dict__[name]

            value = self.db.dict_get(self.get_cache_key(), name)

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
        elif name == 'db':
            return self._trans or self.db_instance
        raise AttributeError('Object instance has no attribute %r' % name)

    def transaction_start(self):
        self._trans = self.db.transaction()

    def transaction_commit(self):
        self._trans.commit()

    def get_cache_key(self, suffix=None):
        key = '%s-%s' % (self.column_family, self.id)
        if suffix:
            key += '-%s' % suffix
        return key

    def initialize(self):
        self.db.list_rpush(self.column_family, self.id)

    def remove(self):
        self.db.list_remove(self.column_family, self.id)
        self.db.remove(self.get_cache_key())

    @classmethod
    def iter_rows(cls):
        for row_id in cls.db_instance.list_iter(cls.column_family):
            row = cls(id=row_id)
            yield row

    @classmethod
    def get_last_row(cls):
        row_id = cls.db_instance.list_index(cls.column_family, -1)
        if row_id:
            return cls(id=row_id)
