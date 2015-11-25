from pritunl.helpers import *
from pritunl import settings
from pritunl import logger
from pritunl import utils

import os
import threading

@interrupter
def _dns_thread():
    while not settings.local.sub_active or \
            settings.local.sub_plan != 'enterprise':
        time.sleep(1)

    return

    while True:
        try:
            utils.check_output_logged(
                ['pritunl-dns'],
                env=dict(os.environ, **{
                    'DB': settings.conf.mongodb_uri,
                    'DB_PREFIX': settings.conf.mongodb_collection_prefix or '',
                }),
            )
        except GeneratorExit:
            raise
        except:
            logger.exception('Error in dns server', 'setup')

        time.sleep(60)
        yield

def setup_dns():
    threading.Thread(target=_dns_thread).start()
