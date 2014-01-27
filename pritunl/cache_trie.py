from constants import *
from cache import cache_db

class CacheTrie(object):
    __slots__ = ('name', 'key')

    def __init__(self, name, key=''):
        self.name = name
        self.key = key

    def get_cache_key(self, suffix=None):
        key = '%s_%s' % (self.name, self.key)
        if suffix is not None:
            key += '_' + suffix
        return key

    def get_nodes(self):
        return cache_db.set_elements(self.get_cache_key())

    def add_value(self, value):
        cache_db.set_add(self.get_cache_key('values'), value)

    def get_values(self):
        return cache_db.set_elements(self.get_cache_key('values'))

    def add_key(self, key, value):
        name = self.name + '_'
        cur_key = self.key
        new_key = cur_key
        for char in key:
            new_key += char
            cache_db.set_add(name + new_key + '_values', value)
            cache_db.set_add(name + cur_key, new_key)
            cur_key = new_key

    def remove_key(self, key, value):
        name = self.name + '_'
        cur_key = self.key
        new_key = cur_key
        for char in key:
            new_key += char
            cache_db.set_remove(name + new_key + '_values', value)
            cache_db.set_remove(name + cur_key, new_key)
            cur_key = new_key

    def _get_iter(self, item):
        return self[item].chain()

    def chain(self, values):
        name = self.name
        for node_key in self.get_nodes():
            CacheTrie(name, node_key).chain(values)
        values.update(self.get_values())
        return values

    def get_prefix(self, prefix):
        return CacheTrie(self.name, prefix).chain(set())

    def iter_prefix(self, prefix):
        for value in CacheTrie(self.name, prefix).chain(set()):
            yield value
