from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
from pritunl.settings import settings
from pritunl import logger

import threading
import urllib2
import json
import time

def load_public_ip(attempts=1, timeout=5):
    for i in xrange(attempts):
        if settings.local.public_ip:
            return
        if i:
            time.sleep(3)
            logger.debug('Retrying get public ip address...')
        logger.debug('Getting public ip address...')
        try:
            request = urllib2.Request(
                settings.app.public_ip_server)
            response = urllib2.urlopen(request, timeout=timeout)
            settings.local.public_ip = json.load(response)['ip']
            break
        except:
            pass
    if not settings.local.public_ip:
        logger.exception('Failed to get public ip address...')

def setup_public_ip():
    #self.load_public_ip()
    if not settings.local.public_ip:
        thread = threading.Thread(target=load_public_ip,
            kwargs={'attempts': 5})
        thread.daemon = True
        thread.start()
