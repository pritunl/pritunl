from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
import time
import threading

class QueueCom(object):
    def __init__(self):
        self.running = threading.Event()
        self.running.set()
        self.last_check = time.time()

    def wait_status(self):
        if not self.running:
            raise QueueStopped('Queue stopped', {
                'queue_id': self.id,
                'queue_type': self.type,
            })
        self.last_check = time.time()
        self.running.wait()
