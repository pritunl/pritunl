from pritunl.helpers import *
from pritunl import messenger
from pritunl import utils

import time

event_queue = utils.NoneQueue()

class Event(object):
    def __init__(self, type, resource_id=None, delay=None):
        if delay:
            # Delay event to reduce duplicate events in short period
            event_queue.put((time.time() + delay, type, resource_id))
            return

        messenger.publish('events', (type, resource_id))

def get_events(cursor=None, yield_app_server=False):
    events = []
    events_dict = {}

    if yield_app_server and check_app_server_interrupt():
        return events

    for event in messenger.subscribe('events', cursor_id=cursor,
            timeout=10, yield_delay=0.02, yield_app_server=yield_app_server):
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
