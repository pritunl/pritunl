from pritunl.constants import *
from pritunl import ipaddress
from pritunl import utils

import threading
import datetime
import random

def setup_demo():
    from pritunl import settings
    from pritunl import server
    from pritunl import host
    from pritunl import link
    from pritunl import mongo
    from pritunl import logger

    if not settings.app.demo_mode:
        return

    def thread():
        platforms = list(DESKTOP_PLATFORMS)
        start_timestamp = datetime.datetime(2015, 12, 28, 4, 1, 0)
        hosts_collection = mongo.get_collection('hosts')
        servers_collection  = mongo.get_collection('servers')
        clients_collection = mongo.get_collection('clients')

        clients_collection.remove({})

        for hst in host.iter_hosts():
            hosts_collection.update({
                '_id': hst.id,
            }, {'$set': {
                'server_count': 0,
                'device_count': 0,
                'cpu_usage': 0,
                'mem_usage': 0,
                'thread_count': 0,
                'open_file_count': 0,
                'status': ONLINE,
                'start_timestamp': start_timestamp,
                'ping_timestamp': start_timestamp,
                'auto_public_address': None,
                'auto_public_address6': None,
                'auto_public_host': hst.name + '.pritunl.com',
                'auto_public_host6': hst.name + '.pritunl.com',
            }})

        for svr in server.iter_servers():
            prefered_hosts = host.get_prefered_hosts(
                svr.hosts, svr.replica_count)

            instances = []
            for hst in prefered_hosts:
                instances.append({
                    'instance_id': utils.ObjectId(),
                    'host_id': hst,
                    'ping_timestamp': utils.now(),
                })

            servers_collection.update({
                '_id': svr.id,
            }, {'$set': {
                'status': ONLINE,
                'pool_cursor': None,
                'start_timestamp': start_timestamp,
                'availability_group': DEFAULT,
                'instances': instances,
                'instances_count': len(instances),
            }})

            for org in svr.iter_orgs():
                for usr in org.iter_users():
                    if usr.type != CERT_CLIENT:
                        continue

                    virt_address = svr.get_ip_addr(org.id, usr.id)
                    virt_address6 = svr.ip4to6(virt_address) + '/64'

                    doc = {
                        '_id': utils.ObjectId(),
                        'user_id': usr.id,
                        'server_id': svr.id,
                        'host_id': settings.local.host_id,
                        'timestamp': start_timestamp,
                        'platform': random.choice(platforms),
                        'type': CERT_CLIENT,
                        'device_name': utils.random_name(),
                        'mac_addr': utils.rand_str(16),
                        'network': svr.network,
                        'real_address': str(
                            ipaddress.ip_address(100000000 + random.randint(
                                0, 1000000000))),
                        'virt_address': virt_address,
                        'virt_address6': virt_address6,
                        'host_address': settings.local.host.local_addr,
                        'host_address6': settings.local.host.local_addr6,
                        'dns_servers': [],
                        'dns_suffix': None,
                        'connected_since': int(start_timestamp.strftime('%s')),
                    }

                    clients_collection.insert(doc)

        for lnk in link.iter_links():
            lnk.status = ONLINE
            lnk.commit()

            for location in lnk.iter_locations():
                active = False
                for hst in location.iter_hosts():
                    if not active:
                        hst.active = True
                        active = True
                    hst.status = AVAILABLE
                    hst.commit(('active', 'status'))

        logger.info('Demo initiated', 'demo')

    thread = threading.Thread(target=thread)
    thread.daemon = True
    thread.start()
