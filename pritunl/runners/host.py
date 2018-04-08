from pritunl.constants import *
from pritunl.helpers import *
from pritunl import settings
from pritunl import host
from pritunl import logger
from pritunl import utils
from pritunl import event
from pritunl import monitoring

import threading
import time
import os
import datetime

@interrupter
def _keep_alive_thread():
    host_event = False
    last_update = None
    proc_stat = None
    settings.local.host_ping_timestamp = utils.now()

    cur_public_ip = None
    cur_public_ip6 = None
    cur_host_name = settings.local.host.name
    cur_route53_region = settings.app.route53_region
    cur_route53_zone = settings.app.route53_zone
    auto_public_host = settings.local.host.auto_public_host
    auto_public_host6 = settings.local.host.auto_public_host6

    while True:
        try:
            if settings.local.host.id != settings.local.host_id:
                logger.error('Host ID mismatch',
                    'runners',
                    host=settings.local.host.id,
                    host_id=settings.local.host_id,
                )

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

            yield interrupter_sleep(settings.app.host_ping)

            ping_timestamp = utils.now()

            try:
                open_file_count = len(os.listdir('/proc/self/fd'))
            except:
                open_file_count = 0

            cpu_usage = None
            mem_usage = None
            thread_count = threading.active_count()
            server_count = len(host.global_servers)
            device_count = host.global_clients.count({})
            try:
                cpu_usage, mem_usage = utils.get_process_cpu_mem()
            except:
                logger.exception('Failed to get process cpu and mem usage',
                    'runners',
                    host_id=settings.local.host_id,
                    host_name=settings.local.host.name,
                )

            host_name = settings.local.host.name
            route53_region = settings.app.route53_region
            route53_zone = settings.app.route53_zone
            if route53_region and route53_zone:
                if cur_public_ip != settings.local.public_ip or \
                        cur_public_ip6 != settings.local.public_ip6 or \
                        cur_host_name != host_name or \
                        cur_route53_region != route53_region or \
                        cur_route53_zone != route53_zone:
                    cur_host_name = host_name
                    cur_public_ip = settings.local.public_ip
                    cur_public_ip6 = settings.local.public_ip6
                    cur_route53_region = route53_region
                    cur_route53_zone = route53_zone

                    auto_public_host, auto_public_host6 = \
                        utils.set_zone_record(
                        route53_region,
                        route53_zone,
                        host_name,
                        cur_public_ip,
                        cur_public_ip6,
                    )

                    settings.local.host.auto_public_host = auto_public_host
                    settings.local.host.auto_public_host6 = auto_public_host6

                    host_event = True
            else:
                auto_public_host = None
                auto_public_host6 = None

            if settings.local.host.auto_public_address != \
                settings.local.public_ip or \
                    settings.local.host.auto_public_address6 != \
                    settings.local.public_ip6:
                settings.local.host.auto_public_address = \
                    settings.local.public_ip
                settings.local.host.auto_public_address6 = \
                    settings.local.public_ip6
                host_event = True

            settings.local.host.collection.update({
                '_id': settings.local.host_id,
            }, {'$set': {
                'version': settings.local.version,
                'server_count': server_count,
                'device_count': device_count,
                'cpu_usage': cpu_usage,
                'mem_usage': mem_usage,
                'thread_count': thread_count,
                'open_file_count': open_file_count,
                'status': ONLINE,
                'ping_timestamp': utils.now(),
                'auto_public_address': settings.local.public_ip,
                'auto_public_address6': settings.local.public_ip6,
                'auto_public_host': auto_public_host,
                'auto_public_host6': auto_public_host6,
            }})

            if host_event:
                host_event = False
                event.Event(type=HOSTS_UPDATED)

            monitoring.insert_point('system', {
                'host': settings.local.host.name,
            }, {
                'cpu_usage': cpu_usage,
                'mem_usage': mem_usage,
                'thread_count': thread_count,
                'open_file_count': open_file_count,
            })

            settings.local.host_ping_timestamp = ping_timestamp
        except GeneratorExit:
            host.deinit()
            raise
        except:
            logger.exception('Error in host keep alive update', 'runners',
                host_id=settings.local.host_id,
                host_name=settings.local.host.name,
            )
            time.sleep(0.5)

def start_host():
    threading.Thread(target=_keep_alive_thread).start()
