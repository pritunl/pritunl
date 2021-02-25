from pritunl.helpers import *
from pritunl import logger
from pritunl import journal
from pritunl import settings

import time
import threading
import json
import os

def rotate():
    base_path = settings.conf.journal_path

    if os.path.exists(base_path + '.5'):
        os.remove(base_path + '.5')

    if os.path.exists(base_path + '.4'):
        os.rename(base_path + '.4', base_path + '.5')

    if os.path.exists(base_path + '.3'):
        os.rename(base_path + '.3', base_path + '.4')

    if os.path.exists(base_path + '.2'):
        os.rename(base_path + '.2', base_path + '.3')

    if os.path.exists(base_path + '.1'):
        os.rename(base_path + '.1', base_path + '.2')

    if os.path.exists(base_path):
        os.rename(base_path, base_path + '.1')

@interrupter
def _journal_runner_thread():
    journal_queue = journal.journal_queue

    while True:
        try:
            while True:
                try:
                    event = journal_queue.popleft()
                    with open(settings.conf.journal_path, 'ab+') as jfile:
                        jfile.write(json.dumps(
                            event,
                            default=lambda x: str(x)
                        ).encode() + '\n'.encode())
                        size = jfile.tell()
                    if size > settings.app.journal_rotate_size:
                        rotate()
                except IndexError:
                    break

            time.sleep(0.25)
            yield

        except GeneratorExit:
            raise
        except:
            logger.exception('Error in journal runner thread', 'runners')
            time.sleep(1)

def start_journal():
    threading.Thread(target=_journal_runner_thread).start()
