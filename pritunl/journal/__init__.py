from pritunl.constants import *
from pritunl import settings
from pritunl import utils

import threading
import json

_journal_queue = utils.PyQueue()

def _get_base_entry(event):
    data = {
        'event': event,
        'timestamp': utils.time_now(),
    }

    data.update(settings.local.host.journal_data)

    return data

def _journal_thread():
    while True:
        event, args, kwargs = _journal_queue.get()
        data = _get_base_entry(event)

        for arg in args:
            data.update(arg)

        data.update(kwargs)

        line = json.dumps(data, default=lambda x: str(x))
        print line

def entry(event, *args, **kwargs):
    _journal_queue.put((event, args, kwargs))

_thread = threading.Thread(target=_journal_thread)
_thread.daemon = True
_thread.start()
