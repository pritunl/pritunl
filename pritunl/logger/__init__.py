from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *

import logging

logger = logging.getLogger(APP_NAME)

def _log(log_level, log_msg, log_type, **kwargs):
    if log_level == 'exception':
        getattr(logger, log_level)(log_msg)
    else:
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
