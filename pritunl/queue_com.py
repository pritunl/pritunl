from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
import time
import threading

class QueueCom(object):
    def __init__(self):
        self.state = RUNNING
        self.state_lock = threading.Lock()
        self.running = threading.Event()
        self.running.set()
        self.last_check = time.time()

    def wait_status(self):
        if self.state in (COMPLETE, STOPPED):
            raise QueueStopped('Queue stopped', {
                'queue_id': self.id,
                'queue_type': self.type,
            })
        self.last_check = time.time()
        self.running.wait()
