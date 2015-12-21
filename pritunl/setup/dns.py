from pritunl.helpers import *
from pritunl import settings
from pritunl import logger

import os
import threading
import subprocess

@interrupter
def _dns_thread():
    from pritunl import host

    while True:
        try:
            if not host.dns_mapping_servers:
                yield interrupter_sleep(3)
                continue

            process = subprocess.Popen(
                ['pritunl-dns'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=dict(os.environ, **{
                    'DB': settings.conf.mongodb_uri,
                    'DB_PREFIX': settings.conf.mongodb_collection_prefix or '',
                }),
            )

            while True:
                if not host.dns_mapping_servers:
                    process.terminate()
                    yield interrupter_sleep(3)
                    process.kill()
                    process = None
                    break
                yield interrupter_sleep(3)
        except GeneratorExit:
            raise
        except:
            logger.exception('Error in monitoring service', 'setup')

        yield interrupter_sleep(1)

def setup_dns():
    threading.Thread(target=_dns_thread).start()
