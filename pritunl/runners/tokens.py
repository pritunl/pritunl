from pritunl.helpers import *
from pritunl import logger
from pritunl import sso

import threading
import time

@interrupter
def tokens_thread():
    while True:
        try:
            time.sleep(3)
            sso.sync_tokens()
        except GeneratorExit:
            raise
        except:
            logger.exception('Error in token sync thread', 'runners')
            time.sleep(1)

        yield

def start_tokens():
    threading.Thread(name="TokensRunner", target=tokens_thread).start()
