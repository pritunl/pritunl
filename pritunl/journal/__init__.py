from pritunl.journal.events import *

from pritunl.constants import *
from pritunl import settings
from pritunl import utils

import threading
import collections
import json

journal_queue = collections.deque()

def get_base_entry(event):
    data = {
        'event': event,
        'timestamp': utils.time_now(),
    }

    data.update(settings.local.host.journal_data)

    return data

def entry(event, *args, **kwargs):
    event = get_base_entry(event)
    for arg in args:
        event.update(arg)
    event.update(kwargs)
    journal_queue.append(event)
