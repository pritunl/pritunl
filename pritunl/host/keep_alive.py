from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
from pritunl.settings import settings
from pritunl.app_server import app_server
from pritunl.host import usage_utils

import threading
import logging
import time

logger = logging.getLogger(APP_NAME)

def _keep_alive_thread(host):
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
                proc_stat = usage_utils.get_proc_stat()

                if last_proc_stat and proc_stat:
                    cpu_usage = usage_utils.calc_cpu_usage(
                        last_proc_stat, proc_stat)
                    mem_usage = usage_utils.get_mem_usage()
                    host.usage.add_period(timestamp, cpu_usage, mem_usage)

            time.sleep(settings.app.host_ttl - 10)

            host.collection.update({
                '_id': host.id,
            }, {'$set': {
                'status': ONLINE,
                'ping_timestamp': datetime.datetime.utcnow(),
                'auto_public_address': app_server.public_ip,
            }})
        except:
            logger.exception('Error in host keep alive update. %s' % {
                'host_id': host.id,
                'host_name': host.name,
            })

def start_keep_alive(host):
    thread = threading.Thread(target=_keep_alive_thread,
        args=(host,))
    thread.daemon = True
    thread.start()
