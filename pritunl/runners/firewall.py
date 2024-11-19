from pritunl.constants import *
from pritunl.helpers import *
from pritunl import logger
from pritunl import settings
from pritunl import firewall

import threading
import time

@interrupter
def _keep_alive_thread():
    while True:
        try:
            time.sleep(1)
            firewall.update()
        except:
            logger.exception('Error in firewall update', 'runners',
                host_id=settings.local.host_id,
                host_name=settings.local.host.name,
            )
            time.sleep(0.5)

def start_firewall():
    threading.Thread(name="FirewallKeepAlive",
        target=_keep_alive_thread).start()
