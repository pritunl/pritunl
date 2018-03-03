from pritunl.helpers import *
from pritunl import utils
from pritunl import logger
from pritunl import app

import threading

@interrupter
def _auto_restart_thread():
    last_run = None

    while True:
        try:
            cur_time = utils.now()

            if int(time.mktime(cur_time.timetuple())) != last_run:
                last_run = int(time.mktime(cur_time.timetuple()))

                if cur_time.hour == 2 and cur_time.minute == 44 and \
                        cur_time.second == 50:
                    app.restart_server_fast()
        except:
            logger.exception('Error in auto restart thread', 'runners')

        time.sleep(0.5)
        yield

def start_auto_restart():
    threading.Thread(target=_auto_restart_thread).start()
