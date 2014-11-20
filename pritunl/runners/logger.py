from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *
from pritunl import utils
from pritunl import logger
from pritunl import mongo
from pritunl import settings

import time
import collections
import threading

@interrupter
def _logger_runner_thread():
    log_queue = logger.log_queue
    collection = mongo.get_collection('logs')

    settings.local.logger_runner = True

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

            yield interrupter_sleep(settings.app.log_db_delay)

        except GeneratorExit:
            raise
        except:
            logger.exception('Error in log runner thread', 'runners')
            time.sleep(0.5)

def start_logger():
    threading.Thread(target=_logger_runner_thread).start()
