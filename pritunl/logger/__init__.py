from pritunl.logger.filter import LogFilter
from pritunl.logger.formatter import LogFormatter
from pritunl.logger.handler import LogHandler, log_queue
from pritunl.logger.entry import *
from pritunl.logger.view import *

from pritunl.constants import *

import logging
import traceback
import threading
import queue

logger = logging.getLogger(APP_NAME)
log_filter = None
log_handler = None
_log_queue = queue.Queue()

def _logger_thread():
    while True:
        args, kwargs = _log_queue.get()
        _log(*args, **kwargs)

def _log(log_level, log_msg, log_type, exc_info=None, **kwargs):
    if not log_filter or not log_handler:
        raise TypeError('Logger not setup')
    getattr(logger, log_level)(
        log_msg,
        exc_info=exc_info,
        extra={
            'type': log_type,
            'data': kwargs,
        },
    )

def debug(log_msg, log_type=None, **kwargs):
    _log_queue.put((
        ('debug', log_msg, log_type),
        kwargs,
    ))

def info(log_msg, log_type=None, **kwargs):
    _log_queue.put((
        ('info', log_msg, log_type),
        kwargs,
    ))

def warning(log_msg, log_type=None, **kwargs):
    _log_queue.put((
        ('warning', log_msg, log_type),
        kwargs,
    ))

def error(log_msg, log_type=None, **kwargs):
    kwargs['traceback'] = traceback.format_stack()
    _log_queue.put((
        ('error', log_msg, log_type),
        kwargs,
    ))

def critical(log_msg, log_type=None, **kwargs):
    kwargs['traceback'] = traceback.format_stack()
    _log_queue.put((
        ('critical', log_msg, log_type),
        kwargs,
    ))

def exception(log_msg, log_type=None, **kwargs):
    # Fix for python #15541
    _log('error', log_msg, log_type, exc_info=True, **kwargs)

_thread = threading.Thread(target=_logger_thread)
_thread.daemon = True
_thread.start()
