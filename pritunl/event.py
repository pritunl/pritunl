from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *
from pritunl import messenger

import time
import bson

class Event(object):
    def __init__(self, type, resource_id=None):
        messenger.publish('events', (type, resource_id))

    def print_caller(self):
        file_name, line_no, func = logger.find_caller()
        file_name = os.path.basename(file_name)
        print 'event: [%s][%s] %s%s' % (
            file_name, line_no, type, resource_id if resource_id else '')

def get_events(cursor=None):
    events = []
    events_dict = {}

    for event in messenger.subscribe('events', cursor_id=cursor,
            timeout=10, yield_delay=0.02):
        event_type, resource_id = event.pop('message')
        if (event_type, resource_id) in events_dict:
            old_event = events_dict[(event_type, resource_id)]
            old_event['id'] = event['_id']
            old_event['timestamp'] = time.mktime(
                event['timestamp'].timetuple())
            continue

        events_dict[(event_type, resource_id)] = event
        event['id'] = event.pop('_id')
        event['type'] = event_type
        event['resource_id'] = resource_id
        event['timestamp'] = time.mktime(event['timestamp'].timetuple())
        event.pop('channel')

        events.append(event)

    return events
