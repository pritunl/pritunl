from pritunl.helpers import *
from pritunl import logger

import threading
import queue

class CallQueue(object):
    def __init__(self, checker=None, maxsize=0):
        if checker is None:
            self._check = check_global_interrupt
        else:
            self._check = checker
        self._close = False
        self._queue = queue.Queue(maxsize)

    def put(self, func, *args, **kwargs):
        self._queue.put((func, args, kwargs))

    def size(self):
        return self._queue.qsize()

    def call(self, timeout=0):
        try:
            func, args, kwargs = self._queue.get(timeout=timeout)
            func(*args, **kwargs)
            return True
        except queue.Empty:
            return False
        except:
            logger.exception('Error in queued called', 'callqueue')

    def _thread(self):
        while True:
            queued = self.call(timeout=0.5)

            if self._check() or (not queued and self._close):
                return

    def start(self, threads=1):
        for _ in range(threads):
            thread = threading.Thread(target=self._thread)
            thread.daemon = True
            thread.start()

    def close(self):
        self._close = True
