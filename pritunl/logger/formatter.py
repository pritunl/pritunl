from pritunl import settings

import logging
import json

class LogFormatter(logging.Formatter):
    def format(self, record):
        from pritunl import plugins

        try:
            host_name = settings.local.host.name
        except AttributeError:
            host_name = 'undefined'
        try:
            host_id = settings.local.host_id
        except AttributeError:
            host_id = 'undefined'

        formatted_record = '[' + host_name + ']'

        try:
            formatted_record += logging.Formatter.format(self, record)
        except:
            try:
                record.msg = record.msg.encode('string_escape')
                formatted_record += logging.Formatter.format(self, record)
            except:
                record.msg = 'Unreadable'
                formatted_record += logging.Formatter.format(self, record)

        kwargs = {
            'message': formatted_record,
            'host_id': host_id,
            'host_name': host_name,
        }

        if hasattr(record, 'data') and record.data:
            kwargs.update(record.data)

            traceback = record.data.pop('traceback', None)
            stdout = record.data.pop('stdout', None)
            stderr = record.data.pop('stderr', None)

            if record.data:
                width = len(max(record.data, key=len))
                for key, val in list(record.data.items()):
                    formatted_record += '\n  %s = %s' % (
                        key.ljust(width),
                        json.dumps(val, default=lambda x: str(x)),
                    )

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

        plugins.event(
            'log_entry',
            **kwargs
        )

        return formatted_record
