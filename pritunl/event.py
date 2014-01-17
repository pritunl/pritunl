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
            events_query = cls.get_rows()
            cursor_found = False
            for event in cls.get_rows():
                if cursor_found:
                    events.append(event)
                elif event.id == cursor:
                    cursor_found = True
            if not cursor_found:
                events = events_query
        else:
            events = cls.get_rows()

        return events
