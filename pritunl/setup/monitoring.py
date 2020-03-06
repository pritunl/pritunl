from pritunl.helpers import *
from pritunl import settings
from pritunl import logger
from pritunl import monitoring

import threading

@interrupter
def _monitoring_thread():
    while True:
        yield interrupter_sleep(settings.app.influxdb_interval)
        try:
            monitoring.connect()
        except:
            logger.exception('InfluxDB connection error',
                'monitoring',
                influxdb_uri=settings.app.influxdb_uri,
            )
            yield interrupter_sleep(5)
            continue

        try:
            monitoring.write_queue()
        except:
            logger.exception('InfluxDB write queue error',
                'monitoring',
                influxdb_uri=settings.app.influxdb_uri,
            )
            yield interrupter_sleep(5)

def setup_monitoring():
    monitoring.init()
    thread = threading.Thread(target=_monitoring_thread)
    thread.daemon = True
    thread.start()
