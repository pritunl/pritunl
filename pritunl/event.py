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

    def dict(self):
        return {
            'id': self.id,
            'type': self.type,
            'resource_id': self.resource_id,
            'time': self.time,
        }

    def initialize(self):
        CacheObject.initialize(self)
        self.db.publish(self.column_family, 'new_event')

    @classmethod
    def get_events(cls, cursor=None, block=True):
        logger.debug('Getting events. %r' % {
            'cursor': cursor,
        })

        while True:
            # Check for events older then ttl
            event_id = cls.db_instance.list_index(cls.column_family, 0)
            if not event_id:
                break
            event_time = cls.db_instance.dict_get('%s-%s' % (
                cls.column_family, event_id), 'time')
            if int(time.time()) - int(event_time) > EVENT_TTL:
                event_id = cls.db_instance.list_lpop(cls.column_family)
                # Expire event to leave time for any get events
                # iterating event list excepting event to still exists
                cls.db_instance.expire('%s-%s' % (cls.column_family, event_id),
                    EVENT_TTL)
            else:
                break

        events = []
        if cursor:
            for event in cls.iter_rows():
                events.append(event)
                if event.id == cursor:
                    events = []
        elif block:
            cursor = cls.db_instance.list_index(cls.column_family, -1)
        else:
            return list(cls.iter_rows())

        if block and not events:
            new_event = False
            for message in cls.db_instance.subscribe(cls.column_family, 30):
                if message == 'new_event':
                    new_event = True
                    break
            if new_event:
                return cls.get_events(cursor, False)

        return events
