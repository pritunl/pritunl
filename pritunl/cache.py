from constants import *
import logging
import time
import collections

logger = logging.getLogger(APP_NAME)

class Cache:
    def __init__(self):
        self._data = collections.defaultdict(
            lambda: {'ttl': None, 'val': None})

    def _check_ttl(self, key):
        if key not in self._data:
            return
        ttl = self._data[key]['ttl']
        if ttl and int(time.time()) > ttl:
            self.remove(self, key)
            return True
        return False

    def get(self, key):
        if self._check_ttl(key) is False:
            return self._data[key]['val']

    def set(self, key, value):
        self._data[key]['val'] = value

    def remove(self, key):
        self._data.pop(key, None)

    def exists(self, key):
        if self._check_ttl(key) is False:
            return True
        return False

    def expire(self, key, ttl):
        timeout = int(time.time()) + ttl
        self._data[key]['ttl'] = timeout

    def set_add(self, key, element):
        try:
            self._data[key]['val'].add(element)
        except AttributeError:
            self._data[key]['val'] = {element}

    def set_remove(self, key, element):
        try:
            self._data[key]['val'].remove(element)
        except (KeyError, AttributeError):
            pass

    def set_elements(self, key):
        if self._check_ttl(key) is False:
            return self._data[key]['val']
        return set()

    def dict_get(self, key, field):
        if self._check_ttl(key) is False:
            return self._data[key]['val'][field]

    def dict_set(self, key, field, value):
        try:
            self._data[key]['val'][field] = value
        except TypeError:
            self._data[key]['val'] = {field: value}

    def dict_remove(self, key, field, value):
        try:
            self._data[key]['val'].pop(field)
        except (KeyError, AttributeError):
            pass

    def dict_get_keys(self, key):
        if self._check_ttl(key) is False:
            return set(self._data[key]['val'].keys())
        return set()

    def dict_get_all(self, key):
        if self._check_ttl(key) is False:
            return self._data[key]['val']
        return {}

cache_db = Cache()
