from pritunl.constants import *
from pritunl.helpers import *
from pritunl import settings
from pritunl import logger
from pritunl import utils

import threading
import urllib2
import json

@interrupter
def _check_updates():
    while True:
        if not settings.app.update_check_rate:
            yield interrupter_sleep(30)
            continue

        try:
            request = urllib2.Request(
                settings.app.notification_server +
                '/%s' % settings.local.version_int)
            response = urllib2.urlopen(request, timeout=60)
            data = json.load(response)

            settings.local.notification = str(data.get('message', ''))
            settings.local.www_state = str(data.get('www', OK))
            settings.local.vpn_state = str(data.get('vpn', OK))
        except:
            logger.exception('Failed to check notifications', 'runners')

        utils.sync_public_ip(update=True)

        yield interrupter_sleep(settings.app.update_check_rate)

def start_updates():
    settings.local.notification = ''
    settings.local.www_state = OK
    settings.local.vpn_state = OK
    threading.Thread(target=_check_updates).start()
