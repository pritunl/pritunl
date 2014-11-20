from pritunl.logger.view import LogView
from pritunl.logger.formatter import LogFormatter

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

    @cached_property
    def file_handler(self):
        log_handler = logging.handlers.RotatingFileHandler(
            settings.conf.log_path, backupCount=1, maxBytes=1000000)
        log_handler.setLevel(logging.DEBUG)
        log_handler.setFormatter(LogFormatter(
            '[%(asctime)s][%(levelname)s] %(message)s'))
        return log_handler

    def emit(self, record):
        msg = self.format(record)

        if not settings.local.logger_runner:
            self.file_handler.emit(record)
        else:
            log_queue.append(msg)

        if not settings.local.quiet:
            print self.log_view.format_line(msg)
