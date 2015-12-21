from pritunl.helpers import *
from pritunl import settings
from pritunl import logger

import os
import threading
import subprocess

@interrupter
def _monitoring_thread():
    while True:
        try:
            mode = settings.app.monitoring
            if not mode:
                yield interrupter_sleep(3)
                continue

            process = subprocess.Popen(
                ['pritunl-monitoring'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=dict(os.environ, **{
                    'HOST_ID': settings.local.host_id,
                    'MODE': mode,
                    'DB': settings.conf.mongodb_uri,
                    'DB_PREFIX': settings.conf.mongodb_collection_prefix or '',
                    'PROMETHEUS_PORT': str(settings.app.prometheus_port),
                    'DATADOG_API_KEY': str(settings.app.datadog_api_key),
                }),
            )

            while True:
                if settings.app.monitoring != mode:
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

def setup_monitoring():
    threading.Thread(target=_monitoring_thread).start()
