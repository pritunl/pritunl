from constants import *
from cache_object import CacheObject
from cache import cache_db
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
            self.initialize()
        else:
            self.id = id

    @classmethod
    def get_events(cls, cursor=None):
        logger.debug('Getting events. %r' % {
            'cursor': cursor,
        })

        while True:
            # Check for events older then ttl
            event_id = cache_db.list_index(cls.column_family, 0)
            if not event_id:
                break
            event_time = cache_db.dict_get('%s-%s' % (
                cls.column_family, event_id), 'time')
            if int(time.time()) - int(event_time) > EVENT_TTL:
                event_id = cache_db.list_lpop(cls.column_family)
                # Expire event to leave time for any get events
                # iterating event list excepting event to still exists
                cache_db.expire('%s-%s' % (cls.column_family, event_id),
                    EVENT_TTL)
            else:
                break

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
