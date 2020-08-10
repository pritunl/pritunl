from pritunl.helpers import *
from pritunl import logger
from pritunl import settings
from pritunl import limiter

import time
import threading

@interrupter
def _limiter_runner_thread():
    while True:
        try:
            for limtr in limiter.limiters:
                cur_time = time.time()
                for peer, (expire, count) in list(limtr.peers_expire_count.items()):
                    if cur_time > expire:
                        limtr.peers_expire_count.pop(peer, None)

            yield interrupter_sleep(settings.app.peer_limit_timeout * 2)

        except GeneratorExit:
            raise
        except:
            logger.exception('Error in limiter runner thread', 'runners')
            time.sleep(0.5)

def start_limiter():
    threading.Thread(target=_limiter_runner_thread).start()
