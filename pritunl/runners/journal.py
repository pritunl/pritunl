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
    rotate_count = settings.app.journal_rotate_count

    oldest_file = base_path + '.' + str(rotate_count)
    if os.path.exists(oldest_file):
        os.remove(oldest_file)

    for i in range(rotate_count - 1, 0, -1):
        current_file = base_path + '.' + str(i)
        next_file = base_path + '.' + str(i + 1)

        if os.path.exists(current_file):
            os.rename(current_file, next_file)

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
    threading.Thread(name="JournalRunner",
        target=_journal_runner_thread).start()
