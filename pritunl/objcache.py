import threading

class ObjCache(object):
    def __init__(self, ttl=60):
        self._ttl = ttl
        self._data = {}
        self._timers = {}

    def remove(self, key):
        self._data.pop(key, None)

    def set(self, key, val):
        cur_timer = self._timers.pop(key, None)
        if cur_timer:
            cur_timer.cancel()

        timer = threading.Timer(self._ttl, self.remove, (key,))
        timer.daemon = True
        self._timers[key] = timer
        timer.start()

        self._data[key] = val

    def get(self, key):
        return self._data.get(key)
