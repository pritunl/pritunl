from pritunl.helpers import *
from pritunl import listener
from pritunl import logger
from pritunl import messenger
from pritunl import callqueue
from pritunl import utils

import threading
import time
import datetime

@interrupter
def listener_thread():
    queue = callqueue.CallQueue()
    queue.start()
    lastlog = utils.now()

    while True:
        try:
            for msg in messenger.subscribe(list(listener.channels.keys())):
                for lstnr in listener.channels[msg['channel']]:
                    try:
                        queue.put(lstnr, msg)

                        size = queue.size()
                        if size >= 50:
                            if utils.now() - lastlog > datetime.timedelta(
                                    minutes=3):
                                lastlog = utils.now()
                                logger.warning(
                                    'Message queue flood',
                                    'runners',
                                    size=size,
                                )
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
