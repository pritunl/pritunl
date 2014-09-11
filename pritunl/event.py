from pritunl.constants import *
from pritunl.messenger import Messenger
import logging
import time
import uuid
import bson

logger = logging.getLogger(APP_NAME)

class Event(object):
    def __init__(self, type, resource_id=None):
        Messenger().publish('events', (type, resource_id))

    @staticmethod
    def get_events(cursor=None):
        events = []
        events_dict = {}
        messenger = Messenger()

        if cursor is not None:
            cursor = bson.ObjectId(cursor)

        for event in messenger.subscribe('events', cursor_id=cursor,
                timeout=10, yield_delay=0.03):
            event_type, resource_id = event.pop('message')
            if (event_type, resource_id) in events_dict:
                old_event = events_dict[(event_type, resource_id)]
                old_event['id'] = str(event['_id'])
                old_event['timestamp'] = time.mktime(
                    event['timestamp'].timetuple())
                continue

            events_dict[(event_type, resource_id)] = event
            event['id'] = str(event.pop('_id'))
            event['type'] = event_type
            event['resource_id'] = resource_id
            event['timestamp'] = time.mktime(event['timestamp'].timetuple())
            event.pop('channel')

            events.append(event)

        return events
