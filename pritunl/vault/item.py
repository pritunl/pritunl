import json

class Item(object):
    def __init__(self, collection, id, key, value, signature=None):
        from pritunl import utils

        if not isinstance(value, str) or value[:8] != '$SEAV1$&':
            value = json.dumps(value, default=utils.json_default)

        self._data = {
            'c': collection,
            'i': json.dumps(id, default=utils.json_default),
            'k': key,
            'v': value,
        }

        if signature:
            self._data['s'] = signature

    @property
    def _id(self):
        return self._data['c'] + '-' + self._data['i'] + '-' + self._data['k']

    @property
    def collection(self):
        return self._data['c']

    @property
    def id(self):
        from pritunl import utils
        return json.loads(
            self._data['s'],
            object_hook=utils.json_object_hook_handler,
        )

    @property
    def key(self):
        return self._data['k']

    @property
    def sig_key(self):
        return self._data['k'] + '_sig'

    @property
    def value(self):
        from pritunl import utils

        val = self._data['v']

        if val[:8] == '$SEAV1$&':
            return val

        return json.loads(
            val,
            object_hook=utils.json_object_hook_handler,
        )

    @property
    def signature(self):
        return self._data['s']

    def encrypt(self):
        self._data['o'] = 'ea1'
        return self

    def decrypt(self):
        self._data['o'] = 'da1'
        return self

    def sign(self):
        self._data['o'] = 'sh1'
        return self

    def verify(self):
        self._data['o'] = 'vh1'
        return self
