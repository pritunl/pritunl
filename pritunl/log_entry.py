from constants import *
from event import Event
from database_object import DatabaseObject
import logging
import time
import uuid

logger = logging.getLogger(APP_NAME)

class LogEntry(DatabaseObject):
    column_family = 'log_entries'
    str_columns = ['type', 'message']
    int_columns = ['time']
    cached_columns = ['type', 'message', 'time']
    required_columns = ['type', 'message', 'time']

    def __init__(self, id=None, type=None, message=None):
        DatabaseObject.__init__(self)

        if id is None:
            self.id = uuid.uuid4().hex
            self.type = type or INFO
            self.time = int(time.time())
            self.message = message
            Event(type=LOG_UPDATED)
        else:
            self.id = id

    @staticmethod
    def get_log_entries():
        logs = []
        logs_dict = {}
        logs_sort = []

        logger.debug('Getting log entries.')

        logs_query = LogEntry.db.get(LogEntry.column_family)
        for log_id in logs_query:
            log = logs_query[log_id]

            if not DatabaseObject.validate(LogEntry, log_id, log):
                continue

            log['time'] = int(log['time'])

            time_id = '%s_%s' % (log['time'], log_id)
            logs_dict[time_id] = LogEntry(id=log_id)
            logs_sort.append(time_id)

        for time_id in reversed(sorted(logs_sort)):
            logs.append(logs_dict[time_id])

        for log in logs[DEFAULT_LOG_LIMIT:]:
            logger.debug('Pruning log entry from database. %r' % {
                'log_id': log.id,
            })
            LogEntry.db.remove(LogEntry.column_family, log.id)

        return logs[:DEFAULT_LOG_LIMIT]
