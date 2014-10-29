from pritunl.logger.filter import LogFilter
from pritunl.logger.formatter import LogFormatter
from pritunl.logger.handler import LogHandler, log_queue
from pritunl.logger.entry import *

from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *
from pritunl import settings

import logging

logger = logging.getLogger(APP_NAME)
log_filter = None
log_handler = None

def find_caller():
    return logger.findCaller()

def _log(log_level, log_msg, log_type, **kwargs):
    if not log_filter or not log_handler:
        raise TypeError('Logger not setup')
    getattr(logger, log_level)(log_msg, extra={
            'type': log_type,
            'data': kwargs,
        })

def debug(log_msg, log_type=None, **kwargs):
    _log('debug', log_msg, log_type, **kwargs)

def info(log_msg, log_type=None, **kwargs):
    _log('info', log_msg, log_type, **kwargs)

def warning(log_msg, log_type=None, **kwargs):
    _log('warning', log_msg, log_type, **kwargs)

def error(log_msg, log_type=None, **kwargs):
    _log('error', log_msg, log_type, **kwargs)

def critical(log_msg, log_type=None, **kwargs):
    _log('critical', log_msg, log_type, **kwargs)

def exception(log_msg, log_type=None, **kwargs):
    _log('exception', log_msg, log_type, **kwargs)
