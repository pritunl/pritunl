from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *
from pritunl import event
from pritunl import settings
from pritunl import subscription

import threading
import time

def _subscription_thread():
    while True:
        time.sleep(SUBSCRIPTION_UPDATE_RATE)
        subscription.update()

def start_subscription():
    settings.local.sub_active = None
    subscription.update()
    thread = threading.Thread(target=_subscription_thread)
    thread.daemon = True
    thread.start()
