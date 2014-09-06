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
    messenger = Messenger('events')

    for event in messenger.subscribe(cursor_id=bson.ObjectId(cursor),
            timeout=10):
        event['id'] = str(event.pop('_id'))
        event['type'], event['resource_id'] = event.pop('message')
        event['timestamp'] = time.mktime(event['timestamp'].timetuple())
        events.append(event)
        break

    return utils.jsonify(events)
