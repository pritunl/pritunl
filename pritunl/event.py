from pritunl.constants import *
from pritunl.cache_object import CacheObject
import logging
import time
import uuid

logger = logging.getLogger(APP_NAME)

class Event(CacheObject):
    column_family = 'events'
    str_columns = {'type', 'resource_id'}
    int_columns = {'timestamp'}
    cached_columns = {'type', 'resource_id', 'timestamp'}

    def __init__(self, id=None, type=None, resource_id=None):
        CacheObject.__init__(self)

        if id is None:
            self.id = uuid.uuid4().hex
            self.type = type
            self.resource_id = resource_id
            self.timestamp = int(time.time())
            self.initialize()
        else:
            self.id = id

    def dict(self):
        return {
            'id': self.id,
            'type': self.type,
            'resource_id': self.resource_id,
            'timestamp': self.timestamp,
        }

    def initialize(self):
        CacheObject.initialize(self)
        self.db.publish(self.column_family, 'new_event')

    @classmethod
    def get_events(cls, cursor=None, block=True):
        while True:
            # Check for events older then ttl
            event_id = cls.db_instance.list_index(cls.column_family, 0)
            if not event_id:
                break
            event_time = cls.db_instance.dict_get('%s-%s' % (
                cls.column_family, event_id), 'timestamp')
            if int(time.time()) - int(event_time) > EVENT_TTL:
                event_id = cls.db_instance.list_lpop(cls.column_family)
                # Expire event to leave time for any get events
                # iterating event list expecting event to still exist
                cls.db_instance.expire('%s-%s' % (cls.column_family, event_id),
                    EVENT_TTL)
            else:
                break

        events = []
        events_set = set()
        if not cursor and block:
            cursor = cls.db_instance.list_index(cls.column_family, -1)
        else:
            for event in cls.iter_rows():
                # Skip duplicate events
                if event.resource_id:
                    key = event.type + '-' + event.resource_id
                else:
                    key = event.type
                if key not in events_set:
                    events_set.add(key)
                    events.append(event)

                if cursor and event.id == cursor:
                    events = []
                    events_set = set()

        if block and not events:
            new_event = False
            for message in cls.db_instance.subscribe(cls.column_family, 30):
                if message == 'new_event':
                    return cls.get_events(cursor, False)

        return events
