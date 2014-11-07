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
            traceback = record.data.pop('traceback', None)
            stdout = record.data.pop('stdout', None)
            stderr = record.data.pop('stderr', None)

            if record.data:
                width = len(max(record.data, key=len))
                for key, val in record.data.items():
                    formatted_record += '\n  %s = %r' % (
                        key.ljust(width), val)
                if stdout:
                    formatted_record += '\nProcess stdout:'
                    stdout_lines = stdout.split('\n')
                    if stdout_lines and not stdout_lines[-1]:
                        stdout_lines.pop()
                    for line in stdout_lines:
                        formatted_record += '\n  ' + line
                if stderr:
                    formatted_record += '\nProcess stderr:'
                    stderr_lines = stderr.split('\n')
                    if stderr_lines and not stderr_lines[-1]:
                        stderr_lines.pop()
                    for line in stderr_lines:
                        formatted_record += '\n  ' + line
                if traceback:
                    formatted_record += \
                        '\nTraceback (most recent call last):\n'
                    formatted_record += ''.join(traceback).rstrip('\n')

        return formatted_record
