from pritunl.helpers import *
from pritunl import listener
from pritunl import logger
from pritunl import messenger
from pritunl import callqueue

import threading
import time

@interrupter
def listener_thread():
    queue = callqueue.CallQueue()
    queue.start(10)

    while True:
        try:
            for msg in messenger.subscribe(listener.channels.keys()):
                for lstnr in listener.channels[msg['channel']]:
                    try:
                        queue.put(lstnr, msg)
                    except:
                        logger.exception('Error in listener callback',
                            'runners')
        except GeneratorExit:
            raise
        except:
            logger.exception('Error in listener thread', 'runners')
            time.sleep(0.3)

        yield

def start_listener():
    threading.Thread(target=listener_thread).start()
