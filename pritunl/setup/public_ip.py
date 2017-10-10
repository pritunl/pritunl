from pritunl import settings
from pritunl import utils

import threading

def setup_public_ip():
    utils.sync_public_ip()
    if not settings.local.public_ip:
        thread = threading.Thread(target=utils.sync_public_ip,
            kwargs={'attempts': 5})
        thread.daemon = True
        thread.start()
