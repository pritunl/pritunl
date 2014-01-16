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
    required_columns = {'type', 'resource_id', 'time'}

    def __init__(self, id=None, type=None, resource_id=None):
        CacheObject.__init__(self)

        if id is None:
            self.id = uuid.uuid4().hex
            self.type = type
            self.resource_id = resource_id
            self.time = int(time.time() * 1000)
            self.expire(EVENT_DB_TTL)
            self.initialize()
        else:
            self.id = id

    @classmethod
    def get_events(cls, last_time=None):
        logger.debug('Getting events. %r' % {
            'last_time': last_time,
        })

        return cls.get_rows(sort_column='time',
            sort_column_min=last_time + 1)
