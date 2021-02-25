from pritunl.logger.view import LogView
from pritunl.logger.formatter import LogFormatter

from pritunl.helpers import *
from pritunl import settings

import logging
import collections
import os

log_queue = collections.deque()

class LogHandler(logging.Handler):
    @cached_property
    def log_view(self):
        return LogView()

    @cached_property
    def file_handler(self):
        path = os.path.dirname(settings.conf.log_path)
        if not os.path.exists(path):
            os.makedirs(path)

        log_handler = logging.handlers.RotatingFileHandler(
            settings.conf.log_path, backupCount=1, maxBytes=1000000)
        log_handler.setLevel(logging.DEBUG)
        log_handler.setFormatter(LogFormatter(
            '[%(asctime)s][%(levelname)s] %(message)s'))

        return log_handler

    def emit(self, record):
        msg = self.format(record)

        if settings.conf.log_path:
            self.file_handler.emit(record)

        if not hasattr(record, 'type') or record.type != 'audit':
            log_queue.append(msg)

        if not settings.local.quiet:
            print(self.log_view.format_line(msg))
