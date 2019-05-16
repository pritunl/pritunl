from pritunl.journal.events import *

from pritunl.constants import *
from pritunl import settings
from pritunl import utils

import collections
import bson

journal_queue = collections.deque()

def get_base_entry(event):
    data = {
        'id': bson.ObjectId(),
        'event': event,
        'timestamp': utils.time_now(),
    }

    data.update(settings.local.host.journal_data)

    return data

def entry(event, *args, **kwargs):
    if settings.app.auditing != ALL:
        return

    event = get_base_entry(event)
    for arg in args:
        event.update(arg)
    event.update(kwargs)
    journal_queue.append(event)
