from constants import *
from pritunl import app_server
from database_object import DatabaseObject
import logging
import time
import uuid

logger = logging.getLogger(APP_NAME)

class Event(DatabaseObject):
    db = app_server.mem_db
    column_family = 'events'
    str_columns = ['type', 'resource_id']
    int_columns = ['time']
    cached_columns = ['type', 'resource_id', 'time']
    required_columns = ['type', 'resource_id', 'time']

    def __init__(self, id=None, type=None, resource_id=None):
        DatabaseObject.__init__(self)

        if id is None:
            self.id = uuid.uuid4().hex
            self.type = type
            self.resource_id = resource_id
            self.time = int(time.time() * 1000)
        else:
            self.id = id

    @staticmethod
    def clean_database():
        cur_time = int(time.time() * 1000)
        events_query = Event.db.get(Event.column_family)
        for event_id in events_query:
            event = events_query[event_id]

            # Skip broken events
            if not DatabaseObject.validate(Event, event_id, event):
                continue

            event['time'] = int(event['time'])

            # Remove events after ttl
            if (cur_time - event['time']) > EVENT_DB_TTL:
                logger.debug('Removing event past ttl from database. %r' % {
                    'event_id': event_id,
                })
                Event.db.remove(Event.column_family, event_id)
                continue

    @staticmethod
    def get_events(last_time=0):
        events = []
        events_dict = {}
        events_sort = []
        cur_time = int(time.time() * 1000)

        logger.debug('Getting events. %r' % {
            'last_time': last_time,
        })

        events_query = Event.db.get(Event.column_family)
        for event_id in events_query:
            event = events_query[event_id]

            # Skip broken events
            if not DatabaseObject.validate(Event, event_id, event):
                continue

            event['time'] = int(event['time'])

            if event['time'] <= last_time:
                continue

            time_id = '%s_%s' % (event['time'], event_id)
            events_dict[time_id] = Event(id=event_id)
            events_sort.append(time_id)

        for time_id in sorted(events_sort):
            events.append(events_dict[time_id])

        return events
