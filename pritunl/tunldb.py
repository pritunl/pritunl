import queue
import time
import collections
import threading
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
    'set_pop',
    'list_lpush',
    'list_rpush',
    'list_lpop',
    'list_rpop',
    'list_remove',
    'dict_set',
    'dict_remove',
}
CHANNEL_TTL = 120
CHANNEL_BUFFER = 128

class TunlDB(object):
    def __init__(self, strict=True):
        self._path = None
        self._set_queue = queue.Queue()
        self._data = collections.defaultdict(
            lambda: {'ttl': None, 'val': None})
        self._timers = {}
        self._channels = collections.defaultdict(
            lambda: {'subs': set(), 'msgs': collections.deque(
                maxlen=CHANNEL_BUFFER), 'timer': None})
        self._commit_log = []
        self._strict = strict

    def _put_queue(self):
        if self._path:
            self._set_queue.put('set')

    def _export_thread(self):
        while True:
            try:
                self._set_queue.get(timeout=5)
            except queue.Empty:
                continue
            # Attempt to get more db sets form queue to reduce export calls
            for _ in range(50):
                try:
                    self._set_queue.get(timeout=0.01)
                except queue.Empty:
                    pass
            self.export_data()

    def _validate(self, value):
        if not self._strict:
            return

        if value is not None and not isinstance(value, str):
            raise TypeError('Value must be string')

    def persist(self, path, auto_export=True):
        if self._path:
            raise ValueError('Persist is already set')
        self._path = path
        self.import_data()
        if auto_export:
            export_thread = threading.Thread(target=self._export_thread)
            export_thread.daemon = True
            export_thread.start()

    def set(self, key, value):
        self._validate(value)
        self._data[key]['val'] = value
        self._put_queue()

    def get(self, key):
        data = self._data.get(key)
        if data:
            return data['val']

    def exists(self, key):
        return key in self._data

    def rename(self, key, new_key):
        data = self._data.get(key)
        if data:
            self._data[new_key]['val'] = data['val']
            self.remove(key)
            self._put_queue()

    def remove(self, key):
        self._data.pop(key, None)
        self._put_queue()

    def expire(self, key, ttl):
        ttl_time = int(time.time() * 1000) + int(ttl * 1000)

        cur_timer = self._timers.pop(key, None)
        if cur_timer:
            cur_timer.cancel()
        timer = threading.Timer(ttl, self.remove, (key,))
        timer.daemon = True
        self._timers[key] = timer
        timer.start()

        self._data[key]['ttl'] = ttl_time
        self._put_queue()

    def increment(self, key):
        value = '1'
        data = self._data.get(key)
        if data:
            try:
                value = str(int(data['val']) + 1)
                data['val'] = value
            except (TypeError, ValueError):
                data['val'] = value
        else:
            self._data[key]['val'] = value
        self._put_queue()
        return value

    def decrement(self, key):
        value = '-1'
        data = self._data.get(key)
        if data:
            try:
                value = str(int(data['val']) - 1)
                data['val'] = value
            except (TypeError, ValueError):
                data['val'] = value
        else:
            self._data[key]['val'] = value
        self._put_queue()
        return value

    def keys(self):
        return set(self._data)

    def set_add(self, key, element):
        self._validate(element)
        data = self._data.get(key)
        if data:
            try:
                data['val'].add(element)
            except AttributeError:
                data['val'] = {element}
        else:
            self._data[key]['val'] = {element}
        self._put_queue()

    def set_remove(self, key, element):
        data = self._data.get(key)
        if data:
            try:
                data['val'].remove(element)
                self._put_queue()
            except (KeyError, AttributeError):
                pass

    def set_pop(self, key):
        value = None
        data = self._data.get(key)
        if data:
            try:
                value = data['val'].pop()
                self._put_queue()
            except (KeyError, AttributeError):
                pass
        return value

    def set_exists(self, key, element):
        data = self._data.get(key)
        if data:
            try:
                return element in data['val']
            except (TypeError, AttributeError):
                pass
        return False

    def set_elements(self, key):
        data = self._data.get(key)
        if data:
            try:
                return data['val'].copy()
            except AttributeError:
                pass
        return set()

    def set_iter(self, key):
        data = self._data.get(key)
        if data:
            try:
                for value in data['val'].copy():
                    yield value
            except AttributeError:
                pass

    def set_length(self, key):
        data = self._data.get(key)
        if data:
            try:
                return len(data['val'])
            except TypeError:
                pass
        return 0

    def list_lpush(self, key, value):
        self._validate(value)
        data = self._data.get(key)
        if data:
            try:
                data['val'].appendleft(value)
            except AttributeError:
                data['val'] = collections.deque([value])
        else:
            self._data[key]['val'] = collections.deque([value])
        self._put_queue()

    def list_rpush(self, key, value):
        self._validate(value)
        data = self._data.get(key)
        if data:
            try:
                data['val'].append(value)
            except AttributeError:
                data['val'] = collections.deque([value])
        else:
            self._data[key]['val'] = collections.deque([value])
        self._put_queue()

    def list_lpop(self, key):
        value = None
        data = self._data.get(key)
        if data:
            try:
                value = data['val'].popleft()
                self._put_queue()
            except (AttributeError, IndexError):
                pass
        return value

    def list_rpop(self, key):
        value = None
        data = self._data.get(key)
        if data:
            try:
                value = data['val'].pop()
                self._put_queue()
            except (AttributeError, IndexError):
                pass
        return value

    def list_index(self, key, index):
        data = self._data.get(key)
        if data:
            try:
                return data['val'][index]
            except (AttributeError, IndexError):
                pass

    def list_elements(self, key):
        data = self._data.get(key)
        if data:
            try:
                return list(data['val'])
            except TypeError:
                pass
        return []

    def list_iter(self, key):
        data = self._data.get(key)
        if data:
            try:
                for value in copy.copy(data['val']):
                    yield value
            except TypeError:
                pass

    def list_iter_range(self, key, start, stop=None):
        data = self._data.get(key)
        if data:
            try:
                for value in itertools.islice(
                        copy.copy(data['val']), start, stop):
                    yield value
            except TypeError:
                pass

    def list_remove(self, key, value, count=1):
        self._validate(value)
        data = self._data.get(key)
        if data:
            if count:
                try:
                    [data['val'].remove(value) for _ in range(count)]
                except (AttributeError, ValueError):
                    pass
            else:
                try:
                    while True:
                        data['val'].remove(value)
                except (AttributeError, ValueError):
                    pass
            self._put_queue()

    def list_length(self, key):
        data = self._data.get(key)
        if data:
            try:
                return len(data['val'])
            except TypeError:
                pass
        return 0

    def dict_set(self, key, field, value):
        self._validate(value)
        data = self._data.get(key)
        if data:
            try:
                data['val'][field] = value
            except TypeError:
                data['val'] = {field: value}
        else:
            self._data[key]['val'] = {field: value}
        self._put_queue()

    def dict_get(self, key, field):
        data = self._data.get(key)
        if data:
            try:
                return data['val'].get(field)
            except TypeError:
                pass

    def dict_remove(self, key, field):
        data = self._data.get(key)
        if data:
            try:
                data['val'].pop(field, None)
            except AttributeError:
                pass
            self._put_queue()

    def dict_keys(self, key):
        data = self._data.get(key)
        if data:
            try:
                return set(data['val'])
            except AttributeError:
                pass
        return set()

    def dict_values(self, key):
        data = self._data.get(key)
        if data:
            try:
                return set(data['val'].values())
            except AttributeError:
                pass
        return set()

    def dict_iter(self, key):
        data = self._data.get(key)
        if data:
            data_copy = data['val'].copy()
            try:
                for field in data_copy:
                    yield field, data_copy[field]
            except (TypeError, AttributeError):
                pass

    def dict_get_all(self, key):
        data = self._data.get(key)
        if data:
            try:
                return data['val'].copy()
            except AttributeError:
                pass
        return {}

    def _clear_channel(self, channel):
        if not self._channels[channel]['subs']:
            self._channels.pop(channel, None)
        else:
            self._channels[channel]['timer'] = None
            self._channels[channel]['msgs'] = collections.deque(
                maxlen=CHANNEL_BUFFER)

    def subscribe(self, channel, timeout=None):
        event = threading.Event()
        self._channels[channel]['subs'].add(event)
        try:
            try:
                cursor = self._channels[channel]['msgs'][-1][0]
            except IndexError:
                cursor = None
            while True:
                if not cursor:
                    cursor_found = True
                else:
                    cursor_found = False
                if not event.wait(timeout):
                    break
                event.clear()
                messages = copy.copy(self._channels[channel]['msgs'])
                for message in messages:
                    if cursor_found:
                        yield message[1]
                    elif message[0] == cursor:
                        cursor_found = True
                if not cursor_found:
                    for message in messages:
                        yield message[1]
                try:
                    cursor = messages[-1][0]
                except IndexError:
                    cursor = None
        finally:
            try:
                self._channels[channel]['subs'].remove(event)
            except KeyError:
                pass

    def publish(self, channel, message):
        cur_timer = self._channels[channel]['timer']
        if cur_timer:
            cur_timer.cancel()
        timer = threading.Timer(CHANNEL_TTL, self._clear_channel, (channel,))
        timer.daemon = True
        self._channels[channel]['timer'] = timer
        timer.start()

        self._channels[channel]['msgs'].append((uuid.uuid4().hex, message))
        for subscriber in self._channels[channel]['subs'].copy():
            subscriber.set()

    def transaction(self):
        return TunlDBTransaction(self)

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
        temp_path = self._path + '_%s.tmp' % uuid.uuid4().hex
        try:
            data = self._data.copy()
            timers = list(self._timers.keys())
            commit_log = copy.copy(self._commit_log)

            with open(temp_path, 'w') as db_file:
                os.chmod(temp_path, 0o600)
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

                    self._data[key] = {
                        'ttl': key_ttl,
                        'val': key_val,
                    }

                if 'timers' in import_data:
                    for key in import_data['timers']:
                        if key not in self._data:
                            continue
                        ttl = self._data[key]['ttl']
                        if not ttl:
                            continue
                        ttl -= int(time.time() * 1000)
                        ttl /= 1000.0
                        if ttl >= 0:
                            timer = threading.Timer(ttl, self.remove, (key,))
                            timer.daemon = True
                            self._timers[key] = timer
                            timer.start()
                        else:
                            self.remove(key)

                if 'commit_log' in import_data:
                    for tran in import_data['commit_log']:
                        self._apply_trans(tran)

class TunlDBTransaction(object):
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
