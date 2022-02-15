# pylama:ignore=E302
import logging

class LogFilter(logging.Filter):
    def filter(self, record):
        return 1
