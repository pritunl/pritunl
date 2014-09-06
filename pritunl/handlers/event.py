from pritunl.constants import *
from pritunl.messenger import Messenger
import pritunl.utils as utils
from pritunl import app_server
import time
import uuid
import flask
import bson

@app_server.app.route('/event', methods=['GET'])
@app_server.app.route('/event/<cursor>', methods=['GET'])
@app_server.auth
def event_get(cursor=None):
    if app_server.interrupt:
        return flask.abort(503)

    events = []
    events_dict = {}
    messenger = Messenger('events')

    for event in messenger.subscribe(cursor_id=bson.ObjectId(cursor),
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
        break

    return utils.jsonify(events)
