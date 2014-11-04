from pritunl.logger.view import LogView

from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *
from pritunl import settings

import logging
import collections

log_queue = collections.deque()

class LogHandler(logging.Handler):
    def __init__(self):
        logging.Handler.__init__(self)

    @cached_property
    def log_view(self):
        return LogView()

    def emit(self, record):
        msg = self.format(record)
        log_queue.append(msg)
        if not settings.local.quiet:
            print self.log_view.format_line(msg)
