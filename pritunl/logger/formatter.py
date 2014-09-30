from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *

import logging

class LogFormatter(logging.Formatter):
    def format(self, record):
        formatted_record = logging.Formatter.format(self, record)
        if hasattr(record, 'data'):
            width = len(max(record.data, key=len))
            for key, val in record.data.items():
                formatted_record += '\n    %s = %r' % (key.ljust(width), val)
        return formatted_record
