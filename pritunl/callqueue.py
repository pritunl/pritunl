import Queue

class CallQueue(object):
    def __init__(self, maxsize=0):
        self._queue = Queue.Queue(maxsize)

    def put(self, func, *args, **kwargs):
        self._queue.put((func, args, kwargs))

    def call(self, timeout=0):
        try:
            func, args, kwargs = self._queue.get(timeout=timeout)
            func(*args, **kwargs)
        except Queue.Empty:
            pass
