from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *
from pritunl import settings

import logging

class LogFormatter(logging.Formatter):
    def format(self, record):
        try:
            host_name = settings.local.host.name
        except AttributeError:
            host_name = 'undefined'

        formatted_record = '[' + host_name + ']' + \
            logging.Formatter.format(self, record)

        if hasattr(record, 'data') and record.data:
            width = len(max(record.data, key=len))
            for key, val in record.data.items():
                formatted_record += '\n    %s = %r' % (key.ljust(width), val)

        return formatted_record
