from pritunl.logger.filter import LogFilter
from pritunl.logger.formatter import LogFormatter
from pritunl.logger.entry import LogEntry

from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *

import logging

_logger_setup = False
_logger = logging.getLogger(APP_NAME)
log_filter = None
log_handler = None

def _log(log_level, log_msg, log_type, **kwargs):
    if not _logger_setup:
        raise TypeError('Logger not setup')
    if log_level == 'exception':
        getattr(_logger, log_level)(log_msg)
    else:
        getattr(_logger, log_level)(log_msg, extra={
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

def setup_logger():
    from pritunl.app_server import app_server
    global _logger_setup
    global log_filter
    global log_handler

    if app_server.log_path:
        log_handler = logging.handlers.RotatingFileHandler(
            app_server.log_path, maxBytes=1000000, backupCount=1)
    else:
        log_handler = logging.StreamHandler()

    log_filter = LogFilter()
    _logger.addFilter(log_filter)

    _logger.setLevel(logging.DEBUG)
    log_handler.setLevel(logging.DEBUG)

    log_handler.setFormatter(LogFormatter(
        '[%(asctime)s][%(levelname)s][%(module)s][%(lineno)d] ' +
        '%(message)s'))

    _logger.addHandler(log_handler)
    _logger_setup = True
