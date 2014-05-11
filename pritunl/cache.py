from constants import *
import Queue
import time
import collections
import threading
import thread
import uuid
import copy
import itertools
import json
import os

TRANSACTION_METHODS = {
    'set',
    'increment',
    'decrement',
    'remove',
    'rename',
    'expire',
    'set_add',
    'set_remove',
    'list_lpush',
    'list_rpush',
    'list_lpop',
    'list_rpop',
    'list_remove',
    'dict_set',
    'dict_remove',
}

class Cache:
    def __init__(self):
        self._path = None
        self._set_queue = Queue.Queue()
        self._data = collections.defaultdict(
            lambda: {'ttl': None, 'val': None})
        self._timers = {}
        self._channels = collections.defaultdict(
            lambda: {'subs': set(), 'msgs': collections.deque(maxlen=64)})
        self._commit_log = []
        self._locks = collections.defaultdict(lambda: threading.Lock())

    def _put_queue(self):
        if self._path:
            self._set_queue.put('set')

    def _export_thread(self):
        from pritunl import app_server
        while not app_server.interrupt:
            try:
                self._set_queue.get(timeout=5)
            except Queue.Empty:
                continue
            # Attempt to get more db sets form queue to reduce export calls
            for i in xrange(50):
                try:
                    self._set_queue.get(timeout=0.01)
                except Queue.Empty:
                    pass
            self.export_data()

    def _validate(self, value):
        if value is not None and not isinstance(value, basestring):
            raise TypeError('Value must be string')

    def _check_ttl(self, key):
        if key not in self._data:
            return
        ttl = self._data[key]['ttl']
        if ttl and int(time.time() * 1000) > ttl:
            self.remove(key)
            return False
        return True

    def _check_ttl_timer(self, key):
        self._timers.pop(key, None)
        self._check_ttl(key)

    def setup_persist(self, path):
        self._path = path
        persist_db.import_data()
        threading.Thread(target=self._export_thread).start()

    def get(self, key):
        if self._check_ttl(key):
            return self._data[key]['val']

    def set(self, key, value):
        self._validate(value)
        self._data[key]['val'] = value
        self._put_queue()

    def increment(self, key):
        if key not in self._data:
            self._data[key]['val'] = '1'
        else:
            try:
                self._data[key]['val'] = str(int(self.get(key)) + 1)
            except (TypeError, ValueError):
                self._data[key]['val'] = '1'
        self._put_queue()

    def decrement(self, key):
        if key not in self._data:
            self._data[key]['val'] = '0'
        else:
            try:
                self._data[key]['val'] = str(int(self.get(key)) - 1)
            except (TypeError, ValueError):
                self._data[key]['val'] = '0'
        self._put_queue()

    def remove(self, key):
        self._data.pop(key, None)
        self._put_queue()

    def rename(self, key, new_key):
        if self._check_ttl(key):
            self._data[new_key]['val'] = self._data[key]['val']
        self.remove(key)
        self._put_queue()

    def exists(self, key):
        if self._check_ttl(key):
            return True
        return False

    def expire(self, key, ttl):
        ttl_time = int(time.time() * 1000) + (ttl * 1000)

        cur_timer = self._timers.pop(key, None)
        timer = threading.Timer(ttl + 0.01, self._check_ttl_timer, (key,))
        self._timers[key] = timer
        if cur_timer:
            cur_timer.cancel()
        timer.start()

        self._data[key]['ttl'] = ttl_time
        self._put_queue()

    def set_add(self, key, element):
        self._validate(element)
        if key not in self._data:
            self._data[key]['val'] = {element}
        else:
            try:
                self._data[key]['val'].add(element)
            except AttributeError:
                self._data[key]['val'] = {element}
        self._put_queue()

    def set_remove(self, key, element):
        try:
            self._data[key]['val'].remove(element)
        except (KeyError, AttributeError):
            pass
        self._put_queue()

    def set_exists(self, key, element):
        if self._check_ttl(key):
            try:
                return element in self._data[key]['val']
            except (TypeError, AttributeError):
                pass
        return False

    def set_elements(self, key):
        if self._check_ttl(key):
            try:
                return self._data[key]['val'].copy()
            except AttributeError:
                pass
        return set()

    def set_length(self, key):
        if self._check_ttl(key):
            try:
                return len(self._data[key]['val'])
            except TypeError:
                pass
        return 0

    def list_lpush(self, key, value):
        self._validate(value)
        if key not in self._data:
            self._data[key]['val'] = collections.deque([value])
        else:
            try:
                self._data[key]['val'].appendleft(value)
            except AttributeError:
                self._data[key]['val'] = collections.deque([value])
        self._put_queue()

    def list_rpush(self, key, value):
        self._validate(value)
        if key not in self._data:
            self._data[key]['val'] = collections.deque([value])
        else:
            try:
                self._data[key]['val'].append(value)
            except AttributeError:
                self._data[key]['val'] = collections.deque([value])
        self._put_queue()

    def list_lpop(self, key):
        data = None
        if self._check_ttl(key):
            try:
                data = self._data[key]['val'].popleft()
            except (AttributeError, IndexError):
                pass
        if data:
            self._put_queue()
            return data

    def list_rpop(self, key):
        data = None
        if self._check_ttl(key):
            try:
                data = self._data[key]['val'].pop()
            except (AttributeError, IndexError):
                pass
        if data:
            self._put_queue()
            return data

    def list_index(self, key, index):
        if self._check_ttl(key):
            try:
                return self._data[key]['val'][index]
            except (AttributeError, IndexError):
                pass

    def list_elements(self, key):
        if self._check_ttl(key):
            try:
                return list(self._data[key]['val'])
            except TypeError:
                pass
        return []

    def list_iter(self, key):
        if self._check_ttl(key):
            try:
                for value in copy.copy(self._data[key]['val']):
                    yield value
            except TypeError:
                pass

    def list_iter_range(self, key, start, stop=None):
        if self._check_ttl(key):
            try:
                for value in itertools.islice(
                        copy.copy(self._data[key]['val']), start, stop):
                    yield value
            except TypeError:
                pass

    def list_remove(self, key, value, count=0):
        self._validate(value)
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
        self._put_queue()

    def list_length(self, key):
        if self._check_ttl(key):
            try:
                return len(self._data[key]['val'])
            except TypeError:
                pass
        return 0

    def dict_get(self, key, field):
        if self._check_ttl(key):
            try:
                return self._data[key]['val'][field]
            except (TypeError, KeyError):
                pass

    def dict_set(self, key, field, value):
        self._validate(value)
        if key not in self._data:
            self._data[key]['val'] = {field: value}
        else:
            try:
                self._data[key]['val'][field] = value
            except TypeError:
                self._data[key]['val'] = {field: value}
        self._put_queue()

    def dict_remove(self, key, field):
        try:
            self._data[key]['val'].pop(field, None)
        except AttributeError:
            pass
        self._put_queue()

    def dict_keys(self, key):
        if self._check_ttl(key):
            try:
                return set(self._data[key]['val'])
            except AttributeError:
                pass
        return set()

    def dict_values(self, key):
        if self._check_ttl(key):
            try:
                return set(self._data[key]['val'].values())
            except AttributeError:
                pass
        return set()

    def dict_get_all(self, key):
        if self._check_ttl(key):
            try:
                return self._data[key]['val'].copy()
            except AttributeError:
                pass
        return {}

    def subscribe(self, channel, timeout=None):
        event = threading.Event()
        self._channels[channel]['subs'].add(event)
        try:
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
        finally:
            self._channels[channel]['subs'].remove(event)

    def publish(self, channel, message):
        self._channels[channel]['msgs'].append(
            (uuid.uuid4().hex, message))
        for subscriber in self._channels[channel]['subs'].copy():
            subscriber.set()

    def lock_acquire(self, key):
        return self._locks[key].acquire()

    def lock_release(self, key):
        try:
            self._locks[key].release()
        except thread.error:
            pass

    def lock_remove(self, key):
        self.lock_release(key)
        self._locks.pop(key, None)

    def transaction(self):
        return CacheTransaction(self)

    def _apply_trans(self, trans):
        for call in trans[1]:
            getattr(self, call[0])(*call[1], **call[2])
        try:
            self._commit_log.remove(trans)
        except ValueError:
            pass
        self._put_queue()

    def export_data(self):
        if not self._path:
            return
        temp_path = self._path + '.tmp'
        try:
            data = self._data.copy()
            timers = self._timers.keys()
            commit_log = copy.copy(self._commit_log)

            with open(temp_path, 'w') as db_file:
                os.chmod(temp_path, 0600)
                export_data = []

                for key in data:
                    key_ttl = data[key]['ttl']
                    key_val = data[key]['val']
                    key_type = type(key_val).__name__
                    if key_type == 'set' or key_type == 'deque':
                        key_val = list(key_val)
                    export_data.append((key, key_type, key_ttl, key_val))

                db_file.write(json.dumps({
                    'ver': 1,
                    'data': export_data,
                    'timers': timers,
                    'commit_log': commit_log,
                }))
            os.rename(temp_path, self._path)
        except:
            try:
                os.remove(temp_path)
            except OSError:
                pass
            raise

    def import_data(self):
        if os.path.isfile(self._path):
            with open(self._path, 'r') as db_file:
                import_data = json.loads(db_file.read())
                data = import_data['data']

                for key_data in data:
                    key = key_data[0]
                    key_type = key_data[1]
                    key_ttl = key_data[2]
                    key_val = key_data[3]

                    if key_type == 'set':
                        key_val = set(key_val)
                    elif key_type == 'deque':
                        key_val = collections.deque(key_val)

                    self._data[key]['ttl'] = key_ttl
                    self._data[key]['val'] = key_val

                if 'timers' in import_data:
                    for key in import_data['timers']:
                        if key not in self._data:
                            continue
                        ttl = self._data[key]['ttl']
                        if not ttl:
                            continue
                        ttl -= int(time.time() * 1000)
                        ttl = ttl / 1000.0
                        if ttl >= 0:
                            timer = threading.Timer(ttl + 0.01,
                                self._check_ttl_timer, (key,))
                            self._timers[key] = timer
                            timer.start()
                        else:
                            self._check_ttl(key)

                if 'commit_log' in import_data:
                    for tran in import_data['commit_log']:
                        self._apply_trans(tran)

class CacheTransaction:
    def __init__(self, cache):
        self._cache = cache
        self._trans = []

    def __getattr__(self, name):
        if name in TRANSACTION_METHODS:
            def serialize(*args, **kwargs):
                self._trans.append((name, args, kwargs))
            return serialize
        return getattr(self._cache, name)

    def commit(self):
        trans = (uuid.uuid4().hex, self._trans)
        self._cache._commit_log.append(trans)
        self._trans = []
        self._cache._apply_trans(trans)

cache_db = Cache()
persist_db = Cache()
