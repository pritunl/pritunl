from constants import *
import logging
import time

logger = logging.getLogger(APP_NAME)

class Cache:
    def __init__(self):
        self._data = {}

    def get(self, key):
        try:
            ttl = self._data[key]['ttl']
            if ttl and int(time.time()) > ttl:
                return
            return self._data[key]['val']
        except KeyError:
            pass

    def set(self, key, value):
        try:
            self._data[key]['val'] = value
        except KeyError:
            self._data[key] = {
                'ttl': None,
                'val': value,
            }

    def remove(self, key):
        self._data.pop(key, None)

    def exists(self, key):
        try:
            ttl = self._data[key]['ttl']
            if not ttl or int(time.time()) <= ttl:
                return True
        except KeyError:
            pass
        return False

    def expire(self, key, ttl):
        timeout = int(time.time()) + ttl
        try:
            self._data[key]['ttl'] = timeout
        except KeyError:
            self._data[key] = {
                'ttl': timeout,
                'val': None,
            }

    def set_add(self, key, element):
        try:
            try:
                self._data[key]['val'].add(element)
            except KeyError:
                self._data[key]['val'] = {element}
        except KeyError:
            self._data[key] = {
                'ttl': None,
                'val': {element},
            }

    def set_remove(self, key, element):
        try:
            self._data[key]['val'].remove(element)
        except (KeyError, AttributeError):
            pass

    def set_elements(self, key):
        try:
            ttl = self._data[key]['ttl']
            if not ttl or int(time.time()) <= ttl:
                return self._data[key]['val']
        except KeyError:
            pass
        return set()

    def dict_get(self, key, field):
        try:
            return self._data[key]['val'][field]
        except KeyError:
            pass

    def dict_set(self, key, field, value):
        try:
            try:
                self._data[key]['val'][field] = value
            except KeyError:
                self._data[key]['val'] = {field: value}
        except KeyError:
            self._data[key] = {
                'ttl': None,
                'val': {field: value},
            }

    def dict_remove(self, key, field, value):
        try:
            self._data[key]['val'].pop(field)
        except (KeyError, AttributeError):
            pass

    def dict_get_all(self, key):
        try:
            ttl = self._data[key]['ttl']
            if not ttl or int(time.time()) <= ttl:
                return self._data[key]['val']
        except KeyError:
            pass
        return {}

cache_db = Cache()
