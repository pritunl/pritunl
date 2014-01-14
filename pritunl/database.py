from constants import *
import threading
import logging
import copy
import urlparse
import time

logger = logging.getLogger(APP_NAME)

class BerkeleyBackend:
    def __init__(self, db_path):
        logger.info('Opening berkeley database... %r' % {
            'path': db_path,
        })

        try:
            import bsddb3 as bsddb
        except ImportError:
            import bsddb

        self._client = bsddb.db.DB()
        try:
            self._client.open(db_path, bsddb.db.DB_HASH, bsddb.db.DB_CREATE)
        except:
            logger.exception('Failed to open berkeley database. %r' % {
                'path': db_path,
            })
            raise
        self._sync_lock = threading.Lock()
        self._sync_interrupt = False
        self._sync_thread = threading.Thread(target=self._sync_loop)
        self._sync_thread.start()

    def _sync_loop(self):
        while not self._sync_interrupt:
            self.sync()
            time.sleep(0.5)
        self.sync()

    def close(self):
        logger.info('Closing berkeley database...')
        self._sync_interrupt = True
        self._sync_thread.join()

    def get(self, key):
        return self._client.get(key=key)

    def set(self, key, value):
        self._client.put(key=key.encode(), data=value)

    def remove(self, key):
        self._client.delete(key=key)

    def keys(self, prefix):
        return self._client.keys()

    def sync(self):
        if self._sync_lock.locked():
            return
        self._sync_lock.acquire()
        try:
            self._client.sync()
        finally:
            self._sync_lock.release()

class MemoryBackend:
    def __init__(self):
        logger.info('Creating memory database...')
        self._data = {}

    def close(self):
        pass

    def get(self, key):
        try:
            return self._data[key]
        except KeyError:
            pass

    def set(self, key, value):
        self._data[key] = value

    def remove(self, key):
        self._data.pop(key, None)

    def keys(self, prefix):
        return self._data.keys()

class Database:
    def __init__(self, db_path):
        self._db_lock = threading.Lock()

        if db_path is None or db_path == 'none':
            self._db = MemoryBackend()
        else:
            self._db = BerkeleyBackend(db_path)

    def _get(self, key):
        self._db_lock.acquire()
        try:
            value = self._db.get(key)
        finally:
            self._db_lock.release()
        return value

    def _prefix_get(self, prefix):
        prefix_len = len(prefix)
        keys = {}

        self._db_lock.acquire()
        try:
            for key in self._db.keys(prefix):
                if key.startswith(prefix):
                    keys[key[prefix_len:]] = self._db.get(key)
        finally:
            self._db_lock.release()

        return keys

    def _set(self, key, value):
        self._db_lock.acquire()
        try:
            self._db.set(key, value)
        finally:
            self._db_lock.release()

    def _remove(self, key):
        self._db_lock.acquire()
        try:
            self._db.remove(key)
        except bsddb.db.DBNotFoundError:
            pass
        finally:
            self._db_lock.release()

    def _prefix_remove(self, prefix):
        prefix_len = len(prefix)

        self._db_lock.acquire()
        try:
            for key in self._db.keys(prefix):
                if key.startswith(prefix):
                    self._db.remove(key)
        finally:
            self._db_lock.release()

    def close(self):
        self._db.close()

    def get(self, column_family, row=None, column=None):
        if not row and column:
            raise TypeError('Must specify a row for column')

        if not row:
            keys = {}
            prefix_keys = self._prefix_get('%s-' % column_family)

            for key in prefix_keys:
                key_split = key.split('-', 1)
                if key_split[0] not in keys:
                    keys[key_split[0]] = {}
                keys[key_split[0]][key_split[1]] = prefix_keys[key]

            return keys

        if not column:
            return self._prefix_get('%s-%s-' % (column_family, row))

        key_name = '%s-%s-%s' % (column_family, row, column)
        return self._get(key_name)

    def set(self, column_family, row, column, value):
        self._set('%s-%s-%s' % (column_family, row, column), value)

    def remove(self, column_family, row=None, column=None):
        if not row and column:
            raise TypeError('Must specify a row for column')

        key_name = '%s-' % column_family
        if row:
            key_name += '%s-' % row

        if not column:
            self._prefix_remove(key_name)
        else:
            key_name += column
            self._remove(key_name)
