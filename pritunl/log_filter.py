from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
import logging

class LogFilter(logging.Filter):
    def filter(self, record):
        if record.levelno == logging.DEBUG:
            log_type = None
            if hasattr(record, 'type'):
                log_type = getattr(record, 'type')
            if log_type not in LOG_DEBUG_TYPES:
                return 0
        return 1
