from constants import *
from cache import cache_db
import itertools

class CacheTrie(object):
    __slots__ = ('prefix', 'key')

    def __init__(self, prefix, key=''):
        self.prefix = prefix
        self.key = key

    def get_nodes(self):
        return cache_db.set_elements('%s_%s' % (self.prefix, self.key))

    def add_value(self, value):
        cache_db.set_add('%s_%s_values' % (self.prefix, self.key), value)

    def get_values(self):
        return cache_db.set_elements('%s_%s_values' % (self.prefix, self.key))

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

    def _yield_values(self):
        yield self.get_values()

    def chain(self):
        chains = map(lambda key: CacheTrie(self.prefix, key).chain(),
            self.get_nodes())
        chains.append(self._yield_values())
        return itertools.chain(*chains)

    def get_prefix(self, prefix):
        values = set()
        prefix_node = CacheTrie(self.prefix, prefix)
        for node_values in prefix_node.chain():
            values.update(node_values)
        return values

    def iter_prefix(self, prefix):
        values = set()
        prefix_node = CacheTrie(self.prefix, prefix)
        for node_values in prefix_node.chain():
            for value in node_values:
                if value not in values:
                    yield value
                    values.add(value)
