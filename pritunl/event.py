from constants import *
from cache_object import CacheObject
import logging
import time
import uuid

logger = logging.getLogger(APP_NAME)

class Event(CacheObject):
    column_family = 'events'
    str_columns = {'type', 'resource_id'}
    int_columns = {'time'}
    cached_columns = {'type', 'resource_id', 'time'}
    required_columns = {'type', 'time'}

    def __init__(self, id=None, type=None, resource_id=None):
        CacheObject.__init__(self)

        if id is None:
            self.id = uuid.uuid4().hex
            self.type = type
            self.resource_id = resource_id
            self.time = int(time.time())
            self.expire(EVENT_DB_TTL)
            self.initialize()
        else:
            self.id = id

    @classmethod
    def get_events(cls, cursor=None):
        logger.debug('Getting events. %r' % {
            'cursor': cursor,
        })

        if cursor:
            events = []
            cursor_found = False
            for event in cls.get_rows():
                if event.id == cursor:
                    cursor_found = True
                    continue
                if not cursor_found:
                    continue
                events.append(event)
        else:
            events = cls.get_rows()

        return events
