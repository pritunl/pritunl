from pritunl.constants import *
from pritunl.event import Event
import pritunl.utils as utils
from pritunl import server
import time
import uuid

@server.app.route('/event', methods=['GET'])
@server.app.route('/event/<int:last_event>', methods=['GET'])
def event_get(last_event=None):
    if not last_event:
        events = [
            {
                'id': uuid.uuid4().hex,
                'type': 'time',
                'time': int(time.time() * 1000),
            },
        ]
        return utils.jsonify(events)

    run_time = 0
    while run_time <= 30 and not server.interrupt:
        events = []

        for event in Event.get_events(last_event):
            events.append({
                'id': event.id,
                'type': event.type,
                'time': event.time
            })

        if len(events):
            return utils.jsonify(events)

        run_time += 0.1
        time.sleep(0.1)

    return utils.jsonify([])
