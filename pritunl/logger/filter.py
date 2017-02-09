import logging

class LogFilter(logging.Filter):
    def filter(self, record):
        return 1
