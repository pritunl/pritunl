from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
from pritunl.settings import settings
from pritunl import logger

import logging

def setup_logger():
    if settings.conf.log_path:
        logger.log_handler = logging.handlers.RotatingFileHandler(
            settings.conf.log_path, maxBytes=1000000, backupCount=1)
    else:
        logger.log_handler = logging.StreamHandler()

    logger.log_filter = logger.LogFilter()
    logger.logger.addFilter(logger.log_filter)

    logger.logger.setLevel(logging.DEBUG)
    logger.log_handler.setLevel(logging.DEBUG)

    logger.log_handler.setFormatter(logger.LogFormatter(
        '[%(asctime)s][%(levelname)s][%(module)s][%(lineno)d] ' +
        '%(message)s'))

    logger.logger.addHandler(logger.log_handler)
