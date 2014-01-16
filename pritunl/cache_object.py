from constants import *
from cache import cache_db

class CacheObject:
    column_family = 'column_family'
    bool_columns = set()
    int_columns = set()
    float_columns = set()
    str_columns = set()
    cached_columns = set()

    def __init__(self):
        self.all_columns = self.bool_columns | self.int_columns | \
            self.float_columns | self.str_columns
        self.id = None

    def __setattr__(self, name, value):
        if name != 'all_columns' and name in self.all_columns:
            if name in self.cached_columns:
                self.__dict__[name] = value

            if name in self.int_columns or name in self.float_columns:
                value = str(value)
            elif name in self.bool_columns:
                value = 't' if value else 'f'

            cache_db.dict_set('%s-%s' % (self.column_family, self.id),
                name, value)
        else:
            self.__dict__[name] = value

    def __getattr__(self, name):
        if name in self.all_columns and self.id:
            if name in self.cached_columns and name in self.__dict__:
                return self.__dict__[name]

            value = cache_db.dict_get(
                '%s-%s' % (self.column_family, self.id), name)

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
        raise AttributeError('Object instance has no attribute %r' % name)

    def initialize(self):
        cache_db.list_append(self.column_family, self.id)

    def expire(self, ttl):
        cache_db.expire(self.column_family, ttl)
        cache_db.expire('%s-%s' % (self.column_family, self.id), ttl)

    def remove(self):
        cache_db.remove(self.column_family)

    @classmethod
    def get_rows(cls):
        rows = []
        for row_id in cache_db.list_elements(cls.column_family):
            row = cls(id=row_id)
            rows.append(row)
        return rows

    @classmethod
    def get_last_row(cls):
        row_id = cache_db.list_index(cls.column_family, -1)
        if row_id:
            return cls(id=row_id)
