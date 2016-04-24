import collections
import re

_keys = collections.defaultdict(
    lambda: collections.defaultdict(lambda: collections.Counter()))
_values = collections.defaultdict(
    lambda: collections.defaultdict(lambda: set()))

class CacheTrie(object):
    __slots__ = ('name', 'key')

    def __init__(self, name, key=''):
        self.name = name
        self.key = key

    def clear_cache(self):
        _keys.pop(self.name, None)
        _values.pop(self.name, None)

    def add_key(self, key, value):
        keys = _keys[self.name]
        cur_key = self.key
        new_key = cur_key
        for char in key.lower():
            new_key += char
            keys[cur_key][new_key] += 1
            cur_key = new_key
        _values[self.name][cur_key].add(value)

    def add_key_terms(self, key, value):
        for term in re.split('[^a-z0-9]', key.lower()):
            self.add_key(term, value)
        self.add_key(key, value)

    def remove_key(self, key, value):
        keys = _keys[self.name]
        values = _values[self.name]
        cur_key = self.key
        new_key = cur_key
        for char in key.lower():
            new_key += char
            keys[cur_key][new_key] -= 1
            if not keys[cur_key][new_key]:
                keys[cur_key].pop(new_key, None)
                if not keys[cur_key]:
                    keys.pop(cur_key, None)
            cur_key = new_key
        try:
            values[cur_key].remove(value)
        except KeyError:
            pass
        if not values[cur_key]:
            values.pop(cur_key, None)

    def remove_key_terms(self, key, value):
        for term in re.split('[^a-z0-9]', key.lower()):
            self.remove_key(term, value)
        self.remove_key(key, value)

    def chain(self, node_values):
        name = self.name
        key = self.key
        keys = _keys[name]
        values = _values[name]
        if key in keys:
            for node_key in keys[key]:
                CacheTrie(name, node_key).chain(node_values)
        if key in values:
            node_values.update(values[key])
        return node_values

    def get_prefix(self, prefix):
        return CacheTrie(self.name, prefix.lower()).chain(set())

    def iter_prefix(self, prefix):
        for value in CacheTrie(self.name, prefix.lower()).chain(set()):
            yield value
