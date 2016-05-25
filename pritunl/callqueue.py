from pritunl.helpers import *
from pritunl import logger

import threading
import Queue

class CallQueue(object):
    def __init__(self, checker=None, maxsize=0):
        if checker is None:
            self._check = check_global_interrupt
        else:
            self._check = checker
        self._queue = Queue.Queue(maxsize)

    def put(self, func, *args, **kwargs):
        self._queue.put((func, args, kwargs))

    def call(self, timeout=0):
        try:
            func, args, kwargs = self._queue.get(timeout=timeout)
            func(*args, **kwargs)
        except Queue.Empty:
            pass
        except:
            logger.exception('Error in queued called', 'callqueue')

    def _thread(self):
        while True:
            self.call(timeout=0.5)

            if self._check():
                return

    def start(self, threads=1):
        for _ in xrange(threads):
            thread = threading.Thread(target=self._thread)
            thread.daemon = True
            thread.start()
