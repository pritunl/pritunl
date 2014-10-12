from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
from pritunl import settings

import logging

def setup_logger():
    from pritunl.app import app
    from pritunl import logger
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
        '[%(asctime)s][%(levelname)s] %(message)s'))

    logger.logger.addHandler(logger.log_handler)

    app.logger.setLevel(logging.DEBUG)
    app.logger.addFilter(logger.log_filter)
    app.logger.addHandler(logger.log_handler)
