from pritunl.constants import *
from pritunl.helpers import *
from pritunl import settings
from pritunl import subscription
from pritunl import logger

import threading

@interrupter
def _subscription_thread():
    while True:
        try:
            yield interrupter_sleep(SUBSCRIPTION_UPDATE_RATE)
            subscription.update()
        except GeneratorExit:
            raise
        except:
            logger.exception('Error in subscription thread', 'runners')

def start_subscription():
    settings.local.sub_active = None
    subscription.update()
    threading.Thread(target=_subscription_thread).start()
