from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
from pritunl.settings import settings
from pritunl.app_server import app_server
from pritunl import host
from pritunl import logger

import threading
import time

def _keep_alive_thread():
    last_update = None
    proc_stat = None

    while True:
        try:
            timestamp = datetime.datetime.utcnow()
            timestamp -= datetime.timedelta(
                microseconds=timestamp.microsecond,
                seconds=timestamp.second,
            )
            if timestamp != last_update:
                last_update = timestamp

                last_proc_stat = proc_stat
                proc_stat = host.usage_utils.get_proc_stat()

                if last_proc_stat and proc_stat:
                    cpu_usage = host.usage_utils.calc_cpu_usage(
                        last_proc_stat, proc_stat)
                    mem_usage = host.usage_utils.get_mem_usage()
                    host.host.usage.add_period(timestamp, cpu_usage, mem_usage)

            time.sleep(settings.app.host_ttl - 10)

            host.host.collection.update({
                '_id': host.host.id,
            }, {'$set': {
                'status': ONLINE,
                'ping_timestamp': datetime.datetime.utcnow(),
                'auto_public_address': settings.local.public_ip,
            }})
        except:
            logger.exception('Error in host keep alive update. %s' % {
                'host_id': host.host.id,
                'host_name': host.host.name,
            })

def start_host():
    thread = threading.Thread(target=_keep_alive_thread)
    thread.daemon = True
    thread.start()
