from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *
from pritunl import settings
from pritunl import logger

import threading
import urllib2
import time
import json

def _check_updates():
    while True:
        if not settings.app.update_check_rate:
            time.sleep(30)
            continue

        logger.debug('Checking notifications...')
        try:
            request = urllib2.Request(
                settings.app.notification_server +
                '/%s' % settings.local.version_int)
            response = urllib2.urlopen(request, timeout=60)
            data = json.load(response)

            settings.local.notification = data.get('message', '')
            settings.local.www_state = data.get('www', OK)
            settings.local.vpn_state = data.get('vpn', OK)
        except:
            logger.exception('Failed to check notifications.')

        logger.debug('Checking subscription status...')
        try:
            pass
            # TODO
            #self.subscription_update()
        except:
            logger.exception('Failed to check subscription status.')
        time.sleep(settings.app.update_check_rate)

def start_updates():
    settings.local.notification = ''
    settings.local.www_state = OK
    settings.local.vpn_state = OK
    thread = threading.Thread(target=_check_updates)
    thread.daemon = True
    thread.start()
