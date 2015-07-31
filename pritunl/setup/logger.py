import logging

def setup_logger():
    from pritunl.app import app
    from pritunl import logger

    logger.log_handler = logger.LogHandler()

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
