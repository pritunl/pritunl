from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *
from pritunl import settings
from pritunl import app
from pritunl import host
from pritunl import logger
from pritunl import utils

import threading
import time

def _keep_alive_thread():
    last_update = None
    proc_stat = None

    while True:
        try:
            timestamp = utils.now()
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
                    settings.local.host.usage.add_period(timestamp,
                        cpu_usage, mem_usage)

            time.sleep(settings.app.host_ttl - 10)

            settings.local.host.collection.update({
                '_id': settings.local.host.id,
            }, {'$set': {
                'status': ONLINE,
                'ping_timestamp': utils.now(),
                'auto_public_address': settings.local.public_ip,
            }})
        except:
            logger.exception('Error in host keep alive update. %s' % {
                'host_id': settings.local.host.id,
                'host_name': settings.local.host.name,
            })

def start_host():
    thread = threading.Thread(target=_keep_alive_thread)
    thread.daemon = True
    thread.start()
