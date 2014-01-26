from constants import *
from cache import cache_db

class CacheTrie(object):
    __slots__ = ('prefix', 'key')

    def __init__(self, prefix, key=''):
        self.prefix = prefix
        self.key = key

    def get_cache_key(self, suffix=None):
        key = '%s_%s' % (self.prefix, self.key)
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
        prefix = self.prefix + '_'
        cur_key = self.key
        new_key = cur_key
        for char in key:
            new_key += char
            cache_db.set_add(prefix + new_key + '_values', value)
            cache_db.set_add(prefix + cur_key, new_key)
            cur_key = new_key

    def _get_iter(self, item):
        return self[item].chain()

    def chain(self, values):
        prefix = self.prefix
        for node_key in self.get_nodes():
            CacheTrie(prefix, node_key).chain(values)
        values.update(self.get_values())
        return values

    def get_prefix(self, prefix):
        return CacheTrie(self.prefix, prefix).chain(set())

    def iter_prefix(self, prefix):
        for value in CacheTrie(self.prefix, prefix).chain(set()):
            yield value
