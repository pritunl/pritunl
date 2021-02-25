from pritunl.helpers import *
from pritunl import event
from pritunl import logger

import time
import threading

@interrupter
def _event_runner_thread():
    evt_queue = event.event_queue
    events = {}
    del_evts = set()

    while True:
        try:
            evt = evt_queue.get(timeout=1)
            if evt is None:
                yield
                continue
            events[(evt[1], evt[2])] = evt[0]

            while True:
                cur_time = time.time()

                for (evt_type, resource_id), evt_time in events.items():
                    if cur_time >= evt_time:
                        event.Event(evt_type, resource_id)
                        del_evts.add((evt_type, resource_id))

                if del_evts:
                    for evt_key in del_evts:
                        try:
                            del events[evt_key]
                        except KeyError:
                            pass
                    del_evts = set()

                if not events:
                    break

                time.sleep(0.025)
                yield

                evt = evt_queue.get_nowait()
                if evt is not None:
                    evt_key = (evt[1], evt[2])
                    if evt_key not in events:
                        events[evt_key] = evt[0]
        except GeneratorExit:
            raise
        except:
            logger.exception('Error in event runner thread.', 'runners')
            time.sleep(0.5)

def start_event():
    threading.Thread(target=_event_runner_thread).start()
