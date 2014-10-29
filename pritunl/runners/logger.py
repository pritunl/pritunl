from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *
from pritunl import utils
from pritunl import logger
from pritunl import mongo

import time
import collections
import threading

@interrupter
def _logger_runner_thread():
    log_queue = logger.log_queue
    collection = mongo.get_collection('log')

    while True:
        try:
            msg_docs = []
            while True:
                try:
                    msg = log_queue.popleft()
                    msg_docs.append({
                        'timestamp': utils.now(),
                        'message': msg,
                    })
                except IndexError:
                    break


            if msg_docs:
                yield

                collection.insert(msg_docs)

            yield interrupter_sleep(3)

        except GeneratorExit:
            raise
        except:
            logger.exception('Error in log runner thread.')
            time.sleep(0.5)

def start_logger():
    threading.Thread(target=_logger_runner_thread).start()
