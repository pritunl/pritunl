from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *
from pritunl import settings
from pritunl import app
from pritunl import host
from pritunl import logger
from pritunl import utils
from pritunl import mongo
from pritunl import event

import threading
import time

@interrupter
def _host_check_thread():
    collection = mongo.get_collection('hosts')

    while True:
        try:
            ttl_timestamp = {'$lt': utils.now() -
                datetime.timedelta(seconds=settings.app.host_ttl)}

            cursor = collection.find({
                'ping_timestamp': ttl_timestamp,
            }, {
                '_id': True,
            })

            for doc in cursor:
                response = collection.update({
                    '_id': doc['_id'],
                    'ping_timestamp': ttl_timestamp,
                }, {'$set': {
                    'status': OFFLINE,
                    'ping_timestamp': None,
                }})

                if response['updatedExisting']:
                    event.Event(type=HOSTS_UPDATED)
        except GeneratorExit:
            raise
        except:
            logger.exception('Error checking host status', 'runners')

        yield interrupter_sleep(settings.app.host_ttl)

@interrupter
def _keep_alive_thread():
    last_update = None
    proc_stat = None
    settings.local.host_ping_timestamp = utils.now()

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

            yield interrupter_sleep(settings.app.host_ttl - 10)

            ping_timestamp = utils.now()

            settings.local.host.collection.update({
                '_id': settings.local.host.id,
            }, {'$set': {
                'status': ONLINE,
                'ping_timestamp': utils.now(),
                'auto_public_address': settings.local.public_ip,
            }})

            settings.local.host_ping_timestamp = ping_timestamp
        except GeneratorExit:
            host.deinit()
            raise
        except:
            logger.exception('Error in host keep alive update. %s' % {
                'host_id': settings.local.host.id,
                'host_name': settings.local.host.name,
            })
            time.sleep(0.5)

def start_host():
    threading.Thread(target=_host_check_thread).start()
    threading.Thread(target=_keep_alive_thread).start()
