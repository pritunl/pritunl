from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *

import logging
import collections

log_queue = collections.deque()

class LogHandler(logging.Handler):
    def __init__(self):
        logging.Handler.__init__(self)

    def emit(self, record):
        msg = self.format(record)
        log_queue.append(msg)
        print msg
