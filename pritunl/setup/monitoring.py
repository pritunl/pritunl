from pritunl.helpers import *
from pritunl import settings
from pritunl import logger
from pritunl import monitoring

import threading

# @interrupter
# def _monitoring_thread():
#     while True:
#         process = None
#
#         try:
#             mode = settings.app.monitoring
#             prometheus_port = settings.app.prometheus_port
#             datadog_api_key = settings.app.datadog_api_key
#             if not mode:
#                 yield interrupter_sleep(3)
#                 continue
#
#             process = subprocess.Popen(
#                 ['pritunl-monitor'],
#                 stdout=subprocess.PIPE,
#                 stderr=subprocess.PIPE,
#                 env=dict(os.environ, **{
#                     'HOST_ID': settings.local.host_id,
#                     'MODE': mode,
#                     'DB': settings.conf.mongodb_uri,
#                     'DB_PREFIX': settings.conf.mongodb_collection_prefix or '',
#                     'PROMETHEUS_PORT': str(prometheus_port),
#                     'DATADOG_API_KEY': str(datadog_api_key),
#                 }),
#             )
#
#             while True:
#                 if settings.app.monitoring != mode or \
#                         settings.app.prometheus_port != prometheus_port or \
#                         settings.app.datadog_api_key != datadog_api_key:
#                     process.terminate()
#                     yield interrupter_sleep(3)
#                     process.kill()
#                     break
#                 elif process.poll() is not None:
#                     output = None
#                     try:
#                         output = process.stdout.readall()
#                         output += process.stderr.readall()
#                     except:
#                         pass
#
#                     logger.error(
#                         'Monitoring service stopped unexpectedly', 'setup',
#                         output=output,
#                     )
#                     break
#
#                 yield interrupter_sleep(3)
#
#             process = None
#         except GeneratorExit:
#             if process:
#                 process.terminate()
#                 time.sleep(1)
#                 process.kill()
#             return
#         except:
#             logger.exception('Error in monitoring service', 'setup')
#
#         yield interrupter_sleep(1)
#
# def setup_monitoring():
#     threading.Thread(target=_monitoring_thread).start()

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
