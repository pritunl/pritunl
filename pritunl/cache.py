from constants import *
import logging
import time
import collections
import threading
import uuid
import copy

logger = logging.getLogger(APP_NAME)

class Cache:
    def __init__(self):
        self._data = collections.defaultdict(
            lambda: {'ttl': None, 'val': None})
        self._channels = collections.defaultdict(
            lambda: {'subs': set(), 'msgs': collections.deque(maxlen=10)})

    def _validate(self, value):
        if value is not None and not isinstance(value, basestring):
            raise TypeError('Value must be string')

    def _check_ttl(self, key):
        if key not in self._data:
            return
        ttl = self._data[key]['ttl']
        if ttl and int(time.time()) > ttl:
            self.remove(key)
            return True
        return False

    def get(self, key):
        if self._check_ttl(key) is False:
            return self._data[key]['val']

    def set(self, key, value):
        self._validate(value)
        self._data[key]['val'] = value

    def increment(self, key):
        try:
            self._data[key]['val'] = str(int(self.get(key)) + 1)
        except (TypeError, ValueError):
            self._data[key]['val'] = 1

    def decrement(self, key):
        try:
            self._data[key]['val'] = str(int(self.get(key)) - 1)
        except (TypeError, ValueError):
            self._data[key]['val'] = 0

    def remove(self, key):
        self._data.pop(key, None)

    def rename(self, key, new_key):
        if self._check_ttl(key) is False:
            self._data[new_key]['val'] = self._data[key]['val']
        self.remove(key)

    def exists(self, key):
        if self._check_ttl(key) is False:
            return True
        return False

    def expire(self, key, ttl):
        timeout = int(time.time()) + ttl
        self._data[key]['ttl'] = timeout

    def set_add(self, key, element):
        self._validate(element)
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
            try:
                return self._data[key]['val'].copy()
            except AttributeError:
                pass
        return set()

    def list_lpush(self, key, value):
        self._validate(value)
        try:
            self._data[key]['val'].appendleft(value)
        except AttributeError:
            self._data[key]['val'] = collections.deque([value])

    def list_rpush(self, key, value):
        self._validate(value)
        try:
            self._data[key]['val'].append(value)
        except AttributeError:
            self._data[key]['val'] = collections.deque([value])

    def list_lpop(self, key):
        if self._check_ttl(key) is False:
            try:
                return self._data[key]['val'].popleft()
            except (AttributeError, IndexError):
                pass

    def list_rpop(self, key):
        if self._check_ttl(key) is False:
            try:
                return self._data[key]['val'].pop()
            except (AttributeError, IndexError):
                pass

    def list_index(self, key, index):
        if self._check_ttl(key) is False:
            try:
                return self._data[key]['val'][index]
            except (AttributeError, IndexError):
                pass

    def list_elements(self, key):
        if self._check_ttl(key) is False:
            try:
                return list(self._data[key]['val'])
            except TypeError:
                pass
        return []

    def list_remove(self, key, value, count=0):
        def _remove():
            try:
                self._data[key]['val'].remove(value)
            except (AttributeError, ValueError):
                return True

        if count:
            for i in xrange(count):
                if _remove():
                    break
        else:
            while True:
                if _remove():
                    break

    def list_length(self, key):
        if self._check_ttl(key) is False:
            try:
                return len(self._data[key]['val'])
            except TypeError:
                pass
        return 0

    def dict_get(self, key, field):
        if self._check_ttl(key) is False:
            try:
                return self._data[key]['val'][field]
            except (TypeError, KeyError):
                pass

    def dict_set(self, key, field, value):
        self._validate(value)
        try:
            self._data[key]['val'][field] = value
        except TypeError:
            self._data[key]['val'] = {field: value}

    def dict_remove(self, key, field):
        try:
            self._data[key]['val'].pop(field, None)
        except AttributeError:
            pass

    def dict_get_keys(self, key):
        if self._check_ttl(key) is False:
            try:
                return set(self._data[key]['val'].keys())
            except AttributeError:
                pass
        return set()

    def dict_get_all(self, key):
        if self._check_ttl(key) is False:
            try:
                return self._data[key]['val'].copy()
            except AttributeError:
                pass
        return {}

    def subscribe(self, channel, timeout=None):
        event = threading.Event()
        self._channels[channel]['subs'].add(event)
        try:
            cursor = self._channels[channel]['msgs'][-1][0]
        except IndexError:
            cursor = None
        while True:
            if not event.wait(timeout):
                break
            event.clear()
            if not cursor:
                cursor_found = True
            else:
                cursor_found = False
            messages = copy.copy(self._channels[channel]['msgs'])
            for message in messages:
                if cursor_found:
                    yield message[1]
                elif message[0] == cursor:
                    cursor_found = True
            cursor = messages[-1][0]

    def publish(self, channel, message):
        self._channels[channel]['msgs'].append(
            (uuid.uuid4().hex, message))
        for subscriber in self._channels[channel]['subs'].copy():
            subscriber.set()

cache_db = Cache()
