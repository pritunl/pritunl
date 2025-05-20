from pritunl.constants import *
from pritunl.helpers import *
from pritunl import utils
from pritunl import mongo
from pritunl import limiter
from pritunl import logger
from pritunl import ipaddress
from pritunl import settings
from pritunl import event
from pritunl import docdb
from pritunl import callqueue
from pritunl import objcache
from pritunl import host
from pritunl import authorizer
from pritunl import messenger
from pritunl import monitoring
from pritunl import plugins
from pritunl import vxlan
from pritunl import journal
from pritunl import database
from pritunl import firewall
from pritunl import callbacks

import time
import collections
import bson
import hashlib
import base64
import binascii
import threading
import uuid
import pymongo
import json
import datetime
import nacl.public
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding

_limiter = limiter.Limiter('vpn', 'peer_limit', 'peer_limit_timeout')

class Clients(object):
    def __init__(self, svr, instance, instance_com):
        self.server = svr
        self.instance = instance
        self.instance_com = instance_com
        self.iroutes = {}
        self.iroutes_thread = {}
        self.iroutes_lock = threading.RLock()
        self.iroutes_index = collections.defaultdict(set)
        self.call_queue = callqueue.CallQueue(
            self.instance.is_interrupted, 512)
        self.clients_call_queue = callqueue.CallQueue(
            self.instance.is_interrupted)
        self.obj_cache = objcache.ObjCache()
        self.client_routes = set()
        self.client_routes6 = set()
        self.link_routes = set()
        self.link_routes6 = set()

        self.clients = docdb.DocDb(
            'user_id',
            'doc_id',
            'mac_addr',
            'virt_address',
        )
        self.clients_queue = collections.deque()
        self.auths_queue = collections.deque()
        self.ip_network = ipaddress.IPv4Network(self.server.network)

        self.firewall_clients = docdb.DocDb(
            'doc_id',
            'user_id',
            'token',
        )

        self.server.generate_auth_key_commit()
        self.server_private_key = self.server.get_auth_private_key()

    @cached_static_property
    def collection(cls):
        return mongo.get_collection('clients')

    @cached_static_property
    def pool_collection(cls):
        return mongo.get_collection('clients_pool')

    @cached_static_property
    def server_collection(cls):
        return mongo.get_collection('servers')

    @cached_property
    def route_addr(self):
        if self.instance.vxlan and self.instance.vxlan.vxlan_addr:
            return self.instance.vxlan.vxlan_addr
        return settings.local.host.local_addr

    @cached_property
    def route_addr6(self):
        if self.instance.vxlan and self.instance.vxlan.vxlan_addr6:
            return self.instance.vxlan.vxlan_addr6
        return settings.local.host.local_addr6

    def get_client(self, client_id):
        client = self.clients.find_id(client_id)
        if not client:
            return None

        return {
            'org_id': client.get('org_id'),
            'org_name': client.get('org_name'),
            'user_id': client.get('user_id'),
            'user_name': client.get('user_name'),
            'device_id': client.get('device_id'),
            'device_name': client.get('device_name'),
            'real_address': client.get('real_address'),
            'virt_address': client.get('virt_address'),
            'virt_address6': client.get('virt_address6'),
        }

    def get_org(self, org_id):
        org = self.obj_cache.get(org_id)
        if not org:
            org = self.server.get_org(org_id, fields=['_id', 'name'])
            if org:
                self.obj_cache.set(org_id, org)
        return org

    def generate_client_conf(self, platform, client_id, virt_address,
            virt_address6, user, reauth, has_token):
        client_conf = ''
        reserved_network_links = []

        client_conf += 'push "ping %s"\n' % self.server.ping_interval
        if settings.app.sso_cache and not self.server.dynamic_firewall and \
            not self.server.device_auth and \
            not self.server.sso_auth and settings.user.reconnect:
            client_conf += 'push "ping-restart %s"\n' % \
                self.server.ping_timeout
        elif (user.has_password(self.server) and has_token) or \
                user.has_passcode(self.server) or \
                user.get_push_type(self.server) or \
                self.server.dynamic_firewall or \
                self.server.device_auth or \
                self.server.sso_auth or \
                not settings.user.reconnect:
            client_conf += 'push "ping-exit %s"\n' % \
                self.server.ping_timeout
        else:
            client_conf += 'push "ping-restart %s"\n' % \
                self.server.ping_timeout

        network_gateway = utils.get_network_gateway(self.server.network)
        network_gateway6 = utils.get_network_gateway(self.server.network6)

        if user.link_server_id:
            link_usr_svr = self.server.get_link_server(user.link_server_id)

            for route in link_usr_svr.get_routes(include_default=False,
                    include_dns_routes=False):
                network = route['network']
                metric = route.get('metric')
                if metric:
                    if ':' in network:
                        metric_def = ' %s %s' % (network_gateway6, metric)
                    else:
                        metric_def = ' vpn_gateway %s' % metric
                else:
                    metric_def = ''

                if route['net_gateway']:
                    continue

                netmap = route.get('nat_netmap')
                if netmap:
                    network = netmap

                if ':' in network:
                    client_conf += 'iroute-ipv6 %s%s\n' % (
                        network, metric_def)
                else:
                    client_conf += 'iroute %s %s%s\n' % (
                        utils.parse_network(network) + (metric_def,))
        else:
            # if self.server.inactive_timeout:
            #     client_conf += 'push "inactive %d"\n' % \
            #         self.server.inactive_timeout

            if self.server.is_route_all():
                client_conf += 'push "redirect-gateway def1"\n'

                if self.server.ipv6 or (settings.vpn.ipv6_route_all and (
                        platform == 'android' or platform == 'ios')):
                    if platform == 'chrome':
                        client_conf += 'push "redirect-gateway ipv6"\n'
                        client_conf += 'push "redirect-gateway-ipv6 def1"\n'
                    else:
                        client_conf += 'push "redirect-gateway ipv6"\n'
                        client_conf += 'push "redirect-gateway-ipv6 def1"\n'
                        client_conf += 'push "route-ipv6 2000::/3"\n'

            if self.server.dns_mapping:
                client_conf += 'push "dhcp-option DNS %s"\n' % (
                    utils.get_network_gateway(self.server.network))

            if not self.server.dns_mapping or \
                    (settings.vpn.dns_mapping_push_all and
                     platform not in ('ios', 'mac')) or \
                    (settings.vpn.dns_mapping_push_all_apple and
                     platform in ('ios', 'mac')):
                for dns_server in self.server.dns_servers:
                    client_conf += 'push "dhcp-option DNS %s"\n' % \
                        dns_server

            if self.server.search_domain:
                domains = self.server.search_domain.split(',')
                for (i, domain) in enumerate(domains):
                    if i == 0:
                        client_conf += 'push "dhcp-option DOMAIN %s"\n' % (
                            domain.strip())
                    client_conf += (
                        'push "dhcp-option DOMAIN-SEARCH %s"\n' % (
                        domain.strip()))

            network_links = user.get_network_links()
            for network_link in network_links:
                if self.reserve_iroute(client_id, network_link, True):
                    reserved_network_links.append(network_link)
                    if ':' in network_link:
                        utils.add_route6(
                            network_link,
                            network_gateway6.split('/')[0],
                            self.instance.interface,
                        )
                        client_conf += 'iroute-ipv6 %s\n' % network_link
                    else:
                        utils.add_route(
                            network_link,
                            network_gateway.split('/')[0],
                            self.instance.interface,
                        )
                        client_conf += 'iroute %s %s\n' % \
                            utils.parse_network(network_link)

            if network_links and not reauth:
                thread = threading.Thread(name="IroutePingOvpn",
                    target=self.iroute_ping_thread,
                    args=(client_id, virt_address.split('/')[0]))
                thread.daemon = True
                thread.start()

            for network_link in self.server.network_links:
                if ':' in network_link:
                    client_conf += 'push "route-ipv6 %s"\n' % network_link
                else:
                    client_conf += 'push "route %s %s"\n' % (
                        utils.parse_network(network_link))

            for link_svr in self.server.iter_links():
                for route in link_svr.get_routes(
                        include_default=False, include_dns_routes=False):
                    network = route['network']
                    metric = route.get('metric')
                    if metric:
                        if ':' in network:
                            metric_def = ' %s %s' % (
                                network_gateway6, metric)
                        else:
                            metric_def = ' vpn_gateway %s' % metric
                        metric = ' %s' % metric
                    else:
                        metric_def = ''
                        metric = ''

                    netmap = route.get('nat_netmap')
                    if netmap:
                        network = netmap

                    if route['net_gateway']:
                        if ':' in network:
                            client_conf += \
                                'push "route-ipv6 %s net_gateway%s"\n' % (
                                network, metric)
                        else:
                            client_conf += \
                                'push "route %s %s net_gateway%s"\n' % (
                                utils.parse_network(network) + (metric,))
                    else:
                        if ':' in network:
                            client_conf += 'push "route-ipv6 %s%s"\n' % (
                                network, metric_def)
                        else:
                            client_conf += 'push "route %s %s%s"\n' % (
                                utils.parse_network(network) + (metric_def,))

                if link_svr.replicating and link_svr.vxlan:
                    client_conf += 'push "route %s %s"\n' % \
                        utils.parse_network(vxlan.get_vxlan_net(link_svr.id))
                    if link_svr.ipv6:
                        client_conf += 'push "route-ipv6 %s"\n' % \
                            vxlan.get_vxlan_net6(link_svr.id)

            if platform == 'android':
                client_conf += 'push "route %s %s"\n' % (
                    utils.parse_network(self.server.network))

                if self.server.ipv6:
                    client_conf += 'push "route-ipv6 %s"\n' % (
                        self.server.network6)

        return client_conf, reserved_network_links

    def generate_client_conf_wg(self, platform, client_id, virt_address,
            virt_address6, user):
        network_gateway = utils.get_network_gateway(self.server.network_wg)
        network_gateway6 = utils.get_network_gateway(self.server.network6_wg)
        reserved_network_links = []

        client_conf = {
            'hostname': settings.local.host.public_addr,
            'hostname6': settings.local.host.public_addr6,
            'gateway': network_gateway,
            'gateway6': network_gateway6,
            'port': self.server.port_wg,
            'mtu': self.server.mss_fix,
            'ping_interval': self.server.ping_interval_wg,
            'ping_timeout': self.server.ping_timeout_wg,
            'web_port': settings.app.server_port,
            'web_no_ssl': not settings.app.server_ssl,
            'public_key': self.instance.wg_public_key,
            'routes': [],
            'routes6': [],
            'dns_servers': [],
            'search_domains': [],
            'network_links': [],
            'network_links6': [],
        }

        if user.link_server_id:
            pass
            # TODO wg
            # link_usr_svr = self.server.get_link_server(user.link_server_id)
            #
            # for route in link_usr_svr.get_routes(include_default=False,
            #         include_dns_routes=False):
            #     network = route['network']
            #     metric = route.get('metric')
            #     if metric:
            #         metric_def = ' vpn_gateway %s' % metric
            #     else:
            #         metric_def = ''
            #
            #     if route['net_gateway']:
            #         continue
            #
            #     netmap = route.get('nat_netmap')
            #     if netmap:
            #         network = netmap
            #
            #     if ':' in network:
            #         client_conf += 'iroute-ipv6 %s%s\n' % (
            #             network, metric_def)
            #     else:
            #         client_conf += 'iroute %s %s%s\n' % (
            #             utils.parse_network(network) + (metric_def,))
        else:
            if self.server.is_route_all():
                client_conf['routes'].append({
                    'next_hop': network_gateway,
                    'network': '0.0.0.0/0',
                })
                if self.server.ipv6:
                    client_conf['routes6'].append({
                        'next_hop': network_gateway6,
                        'network': '::/0',
                    })

            if self.server.dns_mapping:
                client_conf['dns_servers'].append(network_gateway)

            if not self.server.dns_mapping or \
                    (settings.vpn.dns_mapping_push_all and
                     platform not in ('ios', 'mac')) or \
                    (settings.vpn.dns_mapping_push_all_apple and
                     platform in ('ios', 'mac')):
                for dns_server in self.server.dns_servers:
                    client_conf['dns_servers'].append(dns_server)

            if self.server.search_domain:
                for domain in self.server.search_domain.split(','):
                    client_conf['search_domains'].append(domain.strip())

            network_links = user.get_network_links()
            for network_link in network_links:
                if self.reserve_iroute(client_id, network_link, True):
                    reserved_network_links.append(network_link)
                    if ':' in network_link:
                        client_conf['network_links6'].append(network_link)
                        utils.add_route6(
                            network_link,
                            virt_address6.split('/')[0],
                            self.instance.interface_wg,
                        )
                    else:
                        client_conf['network_links'].append(network_link)
                        utils.add_route(
                            network_link,
                            virt_address.split('/')[0],
                            self.instance.interface_wg,
                        )

            if network_links:
                thread = threading.Thread(name="IroutePingWg",
                    target=self.iroute_ping_thread,
                    args=(client_id, virt_address.split('/')[0]))
                thread.daemon = True
                thread.start()

            for link_svr in self.server.iter_links():
                for route in link_svr.get_routes(include_default=False,
                        include_dns_routes=False):
                    network = route['network']
                    metric = route.get('metric')

                    if ':' in network:
                        if network in network_links:
                            continue
                    else:
                        if network in network_links:
                            continue

                    netmap = route.get('nat_netmap')
                    if netmap:
                        network = netmap

                    route_conf = {
                        'network': network,
                    }
                    if metric:
                        route_conf['metric'] = metric

                    if route['net_gateway']:
                        route_conf['net_gateway'] = True

                    if ':' in network:
                        route_conf['next_hop'] = network_gateway6
                        client_conf['routes6'].append(route_conf)
                    else:
                        route_conf['next_hop'] = network_gateway
                        client_conf['routes'].append(route_conf)

                if link_svr.replicating and link_svr.vxlan:
                    client_conf['routes'].append({
                        'next_hop': network_gateway,
                        'network': vxlan.get_vxlan_net(link_svr.id),
                    })
                    if link_svr.ipv6:
                        client_conf['routes6'].append({
                            'next_hop': network_gateway6,
                            'network': vxlan.get_vxlan_net6(link_svr.id),
                        })

            for route in self.server.get_routes(
                    include_default=False,
                    include_dns_routes=self.server.block_outside_dns):
                network = route['network']
                route_conf = {
                    'network': network,
                }

                if ':' in network:
                    if network in network_links:
                        continue
                else:
                    if network in network_links:
                        continue

                if not route['virtual_network']:
                    netmap = route.get('nat_netmap')
                    if netmap:
                        route_conf['network'] = netmap

                    metric = route.get('metric')
                    if metric:
                        route_conf['metric'] = metric

                    if route['net_gateway']:
                        route_conf['net_gateway'] = True

                if ':' in network:
                    route_conf['next_hop'] = network_gateway6
                    client_conf['routes6'].append(route_conf)
                else:
                    route_conf['next_hop'] = network_gateway
                    client_conf['routes'].append(route_conf)

        return client_conf, reserved_network_links

    def reserve_iroute(self, client_id, network, primary):
        reserved = False

        self.iroutes_lock.acquire()
        try:
            self.iroutes_index[client_id].add(network)
            iroute = self.iroutes.get(network)
            reconnect = None

            if iroute and self.clients.count_id(iroute['master']):
                if iroute['master'] == client_id:
                    reserved = True
                elif not primary or iroute['primary']:
                    if primary:
                        iroute['primary_slaves'].add(client_id)
                    else:
                        iroute['secondary_slaves'].add(client_id)
                else:
                    reconnect = iroute['master']
                    iroute['master'] = client_id
                    iroute['primary'] = primary
                    reserved = True
            else:
                self.iroutes[network] = {
                    'master': client_id,
                    'primary': primary,
                    'primary_slaves': set(),
                    'secondary_slaves': set(),
                }
                reserved = True
        finally:
            self.iroutes_lock.release()

        if reconnect:
            self.instance_com.push_output('Primary link available ' +
                'over secondary, relinking %s' % network)
            if len(reconnect) > 32:
                self.instance.disconnect_wg(reconnect, "relink")
            else:
                self.instance_com.client_kill(reconnect, "relink")

        return reserved

    def remove_iroutes(self, client_id):
        primary_reconnect = set()
        secondary_reconnect = set()

        self.iroutes_lock.acquire()
        try:
            if client_id not in self.iroutes_index:
                return

            networks = self.iroutes_index.pop(client_id)
            for network in networks:
                iroute = self.iroutes.get(network)
                if not iroute:
                    continue
                if iroute['master'] == client_id:
                    primary_reconnect |= iroute['primary_slaves']
                    secondary_reconnect |= iroute['secondary_slaves']
                    self.iroutes.pop(network)
                else:
                    if client_id in iroute['primary_slaves']:
                        iroute['primary_slaves'].remove(client_id)
                    if client_id in iroute['secondary_slaves']:
                        iroute['secondary_slaves'].remove(client_id)
        finally:
            self.iroutes_lock.release()

        for client_id in primary_reconnect:
            if len(client_id) > 32:
                self.instance.disconnect_wg(client_id, "primary_reconnect")
            else:
                self.instance_com.client_kill(client_id, "primary_reconnect")

        if primary_reconnect:
            time.sleep(5)

        for client_id in secondary_reconnect:
            if len(client_id) > 32:
                self.instance.disconnect_wg(client_id, "secondary_reconnect")
            else:
                self.instance_com.client_kill(client_id, "secondary_reconnect")

        if primary_reconnect or secondary_reconnect:
            self.instance_com.push_output('Gateway link ' +
                'changed, relinking gateways')

    def has_failover_iroute(self, client_id):
        self.iroutes_lock.acquire()

        try:
            if client_id in self.iroutes_index:
                for network in self.iroutes_index[client_id]:
                    iroute = self.iroutes.get(network)

                    if iroute['primary_slaves'] or iroute['primary_slaves']:
                        return True
            else:
                return True
        finally:
            self.iroutes_lock.release()

        return False

    def get_virt_addr(self, org_id, user_id, mac_addr, doc_id, final=False):
        address_dynamic = False
        disconnected = set()
        subnet = '/%s' % self.ip_network.prefixlen

        virt_address = self.server.get_ip_addr(org_id, user_id)
        if not virt_address:
            self.server.reset_ip_pool()

            logger.error('User missing ip address',
                'clients',
                server_id=self.server.id,
                instance_id=self.instance.id,
                user_id=user_id,
                multi_device=self.server.multi_device,
                network=self.server.network,
                user_count=self.server.user_count,
            )

        if virt_address and self.server.multi_device:
            device_found = False

            if mac_addr:
                doc = self.pool_collection.find_one({
                    'server_id': self.server.id,
                    'user_id': user_id,
                    'mac_addr': mac_addr,
                })
                if doc:
                    orig_virt_address = virt_address
                    virt_address = utils.long_to_ip(doc['_id']) + subnet

                    response = self.pool_collection.update_one({
                        '_id': doc['_id'],
                        'server_id': self.server.id,
                        'user_id': user_id,
                        'mac_addr': mac_addr,
                    }, {'$set': {
                        'server_id': self.server.id,
                        'user_id': user_id,
                        'mac_addr': mac_addr,
                        'client_id': doc_id,
                        'timestamp': utils.now(),
                        'static': True,
                    }})

                    if bool(response.modified_count):
                        device_found = True
                        messenger.publish('instance', [
                            'user_disconnect_id',
                            user_id,
                            doc['client_id'],
                            self.server.id,
                        ])
                        disconnected.add(doc['client_id'])
                    else:
                        virt_address = orig_virt_address

            if not device_found:
                doc = self.pool_collection.find_one({
                    '_id': utils.ip_to_long(
                        virt_address.split('/')[0]),
                })
                if doc:
                    if doc['server_id'] == self.server.id and \
                            doc['user_id'] == user_id and \
                            mac_addr and doc['mac_addr'] == mac_addr:
                        response = self.pool_collection.update_one({
                            '_id': utils.ip_to_long(
                                virt_address.split('/')[0]),
                            'server_id': self.server.id,
                            'user_id': user_id,
                            'mac_addr': mac_addr,
                        }, {'$set': {
                            'server_id': self.server.id,
                            'user_id': user_id,
                            'mac_addr': mac_addr,
                            'client_id': doc_id,
                            'timestamp': utils.now(),
                            'static': True,
                        }})

                        if bool(response.modified_count):
                            messenger.publish('instance', [
                                'user_disconnect_id',
                                user_id,
                                doc['client_id'],
                                self.server.id,
                            ])
                            disconnected.add(doc['client_id'])
                        else:
                            virt_address = None
                    else:
                        virt_address = None
                else:
                    try:
                        self.pool_collection.insert_one({
                            '_id': utils.ip_to_long(
                                virt_address.split('/')[0]),
                            'server_id': self.server.id,
                            'user_id': user_id,
                            'mac_addr': mac_addr,
                            'client_id': doc_id,
                            'timestamp': utils.now(),
                            'static': True,
                        })
                    except pymongo.errors.DuplicateKeyError:
                        virt_address = None

                if mac_addr:
                    messenger.publish('instance', [
                        'user_disconnect_mac',
                        user_id,
                        settings.local.host_id,
                        mac_addr,
                        self.server.id,
                    ])

        if not virt_address:
            doc = self.pool_collection.find_one_and_replace({
                'server_id': self.server.id,
                'user_id': None,
            }, {
                'server_id': self.server.id,
                'user_id': user_id,
                'mac_addr': mac_addr,
                'client_id': doc_id,
                'timestamp': utils.now(),
                'static': False,
            }, return_document=True)

            if doc:
                address_dynamic = True
                virt_address = utils.long_to_ip(doc['_id']) + subnet
            else:
                doc = self.server_collection.find_one({
                    '_id': self.server.id,
                }, {
                    'pool_cursor': True,
                })
                last_addr = doc.get('pool_cursor')

                if last_addr:
                    last_addr = ipaddress.IPv4Address(
                        utils.long_to_ip(last_addr))

                network = ipaddress.IPv4Network(self.server.network)
                ip_pool = utils.get_ip_pool_reverse(network, last_addr)

                if ip_pool:
                    for ip_addr in ip_pool:
                        try:
                            self.pool_collection.insert_one({
                                '_id': int(ip_addr._ip),
                                'server_id': self.server.id,
                                'user_id': user_id,
                                'mac_addr': mac_addr,
                                'client_id': doc_id,
                                'timestamp': utils.now(),
                                'static': False,
                            })
                            virt_address = str(ip_addr) + subnet
                            address_dynamic = True
                            break
                        except pymongo.errors.DuplicateKeyError:
                            continue

                    if virt_address:
                        self.server_collection.update_one({
                            '_id': self.server.id,
                            'status': ONLINE,
                        }, {'$set': {
                            'pool_cursor': utils.ip_to_long(
                                virt_address.split('/')[0]),
                        }})

        if not virt_address:
            if not final:
                logger.info('Unable to assign ip address, retrying',
                    'clients',
                    server_id=self.server.id,
                    instance_id=self.instance.id,
                    user_id=user_id,
                    multi_device=self.server.multi_device,
                    replica_count=self.server.replica_count,
                    network=self.server.network,
                    user_count=self.server.user_count,
                )
                self.server.reset_ip_pool()
                return self.get_virt_addr(
                    org_id, user_id, mac_addr, doc_id, True)

            logger.error('Unable to assign ip address, pool full',
                'clients',
                server_id=self.server.id,
                instance_id=self.instance.id,
                user_id=user_id,
                multi_device=self.server.multi_device,
                replica_count=self.server.replica_count,
                network=self.server.network,
                user_count=self.server.user_count,
            )

        if self.server.multi_device and self.server.max_devices:
            if not virt_address:
                raise ValueError('Failed to get virtual address')

            cur_id = utils.ip_to_long(virt_address.split('/')[0])
            conn_count = 0
            docs = self.pool_collection.find({
                'server_id': self.server.id,
                'user_id': user_id,
            })

            for doc in docs:
                if doc['_id'] == cur_id:
                    continue

                if conn_count > self.server.max_devices:
                    messenger.publish('instance', [
                        'user_disconnect_id',
                        user_id,
                        doc['client_id'],
                        self.server.id,
                    ])
                    continue

                conn_count += 1

            if conn_count >= self.server.max_devices:
                if address_dynamic:
                    self.pool_collection.update_one({
                        'server_id': self.server.id,
                        'user_id': user_id,
                        'client_id': doc_id,
                    }, {'$set': {
                        'user_id': None,
                        'mac_addr': None,
                        'client_id': None,
                        'timestamp': None,
                    }})
                else:
                    self.pool_collection.delete_one({
                        'server_id': self.server.id,
                        'user_id': user_id,
                        'client_id': doc_id,
                        'static': True,
                    })
                return None, False, True

        return virt_address, address_dynamic, False

    def allow_client(self, client_data, org, user, password, reauth=False,
            has_token=False, doc_id=None):
        client_id = client_data['client_id']
        key_id = client_data['key_id']
        org_id = client_data['org_id']
        user_id = client_data['user_id']
        device_id = client_data.get('device_id')
        device_name = client_data.get('device_name')
        platform = client_data.get('platform')
        client_ver = client_data.get('client_ver')
        mac_addr = client_data.get('mac_addr')
        remote_ip = client_data.get('remote_ip')

        if not doc_id:
            doc_id = database.ObjectId()

        if reauth:
            doc = self.clients.find_id(client_id)
            if not doc:
                self.instance_com.send_client_deny(client_id, key_id,
                    'Client connection info timed out')
                return

            virt_address = doc['virt_address']
            virt_address6 = doc['virt_address6']
        else:
            user.audit_event(
                'user_connection',
                'User connected to "%s"' % self.server.name,
                remote_addr=remote_ip,
                server_name=self.server.name,
            )
            monitoring.insert_point('user_connections', {
                'host': settings.local.host.name,
                'server': self.server.name,
            }, {
                'user': user.name,
                'type': 'ovpn',
                'platform': utils.filter_str2(platform),
                'remote_ip': remote_ip,
            })

            user.last_active = utils.now()
            user.commit('last_active')

            virt_address, address_dynamic, device_limit = \
                self.get_virt_addr(org_id, user_id, mac_addr, doc_id)

            if device_limit:
                self.instance_com.send_client_deny(client_id, key_id,
                    'Too many devices')
                return

            if not self.server.multi_device:
                if self.server.replicating:
                    # if self.server.route_clients:
                    #     docs = self.collection.find({
                    #         'user_id': user_id,
                    #         'server_id': self.server.id,
                    #     })
                    #
                    #     for doc in docs:
                    #         messenger.publish('client', {
                    #             'state': False,
                    #             'server_id': self.server.id,
                    #             'virt_address': doc['virt_address'],
                    #             'virt_address6': doc['virt_address6'],
                    #             'host_address': doc['host_address'],
                    #             'host_address6': doc['host_address6'],
                    #         })
                    #
                    #     docs = self.collection.find({
                    #         'user_id': user_id,
                    #         'server_id': self.server.id,
                    #     })
                    #
                    #     for doc in docs:
                    #         network_links = doc.get('network_links')
                    #         if not network_links:
                    #             continue
                    #
                    #         messenger.publish('client_links', {
                    #             'state': False,
                    #             'server_id': self.server.id,
                    #             'virt_address': doc['virt_address'],
                    #             'virt_address6': doc['virt_address6'],
                    #             'host_address': doc['host_address'],
                    #             'host_address6': doc['host_address6'],
                    #             'network_links': network_links,
                    #         })

                    messenger.publish('instance', [
                        'user_reconnect',
                        user_id,
                        settings.local.host_id,
                        self.server.id,
                    ])

                for clnt in self.clients.find({'user_id': user_id}):
                    time.sleep(2)
                    if len(clnt['id']) > 32:
                        self.instance.disconnect_wg(clnt['id'],
                            "remove_multi")
                    else:
                        self.instance_com.client_kill(clnt['id'],
                            "remove_multi")

            if not virt_address:
                self.instance_com.send_client_deny(client_id, key_id,
                    'Unable to assign ip address')
                return

            virt_address6 = self.server.ip4to6(virt_address) + '/64'

            dns_servers = []
            if user.dns_servers:
                for dns_server in user.dns_servers:
                    if dns_server == '127.0.0.1':
                        dns_server = virt_address
                    dns_servers.append(dns_server)

            rules, rules6 = self.generate_iptables_rules(
                user, virt_address, virt_address6)

            self.clients.insert({
                'id': client_id,
                'type': 'ovpn',
                'doc_id': doc_id,
                'org_id': org_id,
                'org_name': org.name,
                'user_id': user_id,
                'user_name': user.name,
                'user_type': user.type,
                'timestamp': time.time(),
                'timestamp_start': time.time(),
                'auth_check_timestamp': time.time(),
                'password': password,
                'dns_servers': dns_servers,
                'dns_suffix': user.dns_suffix,
                'device_id': device_id,
                'device_name': device_name,
                'platform': platform,
                'client_ver': client_ver,
                'mac_addr': mac_addr,
                'virt_address': virt_address,
                'virt_address6': virt_address6,
                'real_address': remote_ip,
                'address_dynamic': address_dynamic,
                'iptables_rules': rules,
                'ip6tables_rules': rules6,
            })

            if user.type == CERT_CLIENT:
                plugins.event(
                    'user_connected',
                    host_id=settings.local.host_id,
                    server_id=self.server.id,
                    org_id=org.id,
                    user_id=user.id,
                    host_name=settings.local.host.name,
                    server_name=self.server.name,
                    org_name=org.name,
                    user_name=user.name,
                    platform=platform,
                    client_ver=client_ver,
                    device_id=device_id,
                    device_name=device_name,
                    virtual_ip=virt_address,
                    virtual_ip6=virt_address6,
                    remote_ip=remote_ip,
                    mac_addr=mac_addr,
                )
                host.global_clients.insert({
                    'instance_id': self.instance.id,
                    'client_id': client_id,
                })

        client_conf, network_links = self.generate_client_conf(
            platform, client_id, virt_address, virt_address6, user,
            reauth, has_token)

        self.clients.update_id(client_id, {
            'network_links': network_links,
        })

        client_conf += 'ifconfig-push %s %s\n' % utils.parse_network(
            virt_address)

        if self.server.ipv6:
            client_conf += 'ifconfig-ipv6-push %s\n' % virt_address6

        if self.server.debug:
            self.instance_com.push_output('Client conf %s:' % user_id)
            for conf_line in client_conf.split('\n'):
                if conf_line:
                    self.instance_com.push_output('  ' + conf_line)

        self.instance_com.send_client_auth(client_id, key_id, client_conf)

    def allow_client_wg(self, user, org, wg_public_key, platform, client_ver,
            device_id, device_name, password, mac_addr, client_public_address,
            client_public_address6, remote_ip):
        try:
            user_id = user.id
            org_id = org.id
            client_id = wg_public_key
            doc_id = database.ObjectId()

            user.audit_event(
                'user_connection_wg',
                'User connected wg to "%s"' % self.server.name,
                remote_addr=remote_ip,
                server_name=self.server.name,
            )
            monitoring.insert_point('user_connections', {
                'host': settings.local.host.name,
                'server': self.server.name,
            }, {
                'user': user.name,
                'type': 'wg',
                'platform': utils.filter_str2(platform),
                'remote_ip': remote_ip,
            })

            user.last_active = utils.now()
            user.commit('last_active')

            virt_address, address_dynamic, device_limit = \
                self.get_virt_addr(org_id, user_id, mac_addr, doc_id)

            if device_limit:
                self.instance.disconnect_wg(wg_public_key, "device_limit")
                return False, 'Too many devices'

            if not self.server.multi_device:
                if self.server.replicating:
                    messenger.publish('instance', [
                        'user_reconnect',
                        user_id,
                        settings.local.host_id,
                        self.server.id,
                    ])

                for clnt in self.clients.find({'user_id': user_id}):
                    time.sleep(2)
                    if len(clnt['id']) > 32:
                        self.instance.disconnect_wg(clnt['id'],
                            "remove_multi_wg")
                    else:
                        self.instance_com.client_kill(clnt['id'],
                            "remove_multi_wg")

            if not virt_address:
                self.instance.disconnect_wg(wg_public_key, "no_virt_address")
                return False, 'Unable to assign ip address'

            virt_address = self.server.ip4to4wg(virt_address)
            virt_address6 = self.server.ip4to6wg(virt_address) + '/64'

            dns_servers = []
            if user.dns_servers:
                for dns_server in user.dns_servers:
                    if dns_server == '127.0.0.1':
                        dns_server = virt_address
                    dns_servers.append(dns_server)

            rules, rules6 = self.generate_iptables_rules_wg(
                user, virt_address, virt_address6)

            self.clients.insert({
                'id': client_id,
                'type': 'wg',
                'doc_id': doc_id,
                'org_id': org.id,
                'org_name': org.name,
                'user_id': user.id,
                'user_name': user.name,
                'user_type': user.type,
                'timestamp': time.time(),
                'timestamp_start': time.time(),
                'timestamp_wg': time.time(),
                'auth_check_timestamp': time.time(),
                'password': password,
                'dns_servers': dns_servers,
                'dns_suffix': user.dns_suffix,
                'device_id': device_id,
                'device_name': device_name,
                'platform': platform,
                'client_ver': client_ver,
                'mac_addr': mac_addr,
                'virt_address': virt_address,
                'virt_address6': virt_address6,
                'real_address': remote_ip,
                'address_dynamic': address_dynamic,
                'iptables_rules': rules,
                'ip6tables_rules': rules6,
                'wg_public_key': wg_public_key,
            })

            if user.type == CERT_CLIENT:
                plugins.event(
                    'user_connected',
                    host_id=settings.local.host_id,
                    server_id=self.server.id,
                    org_id=org.id,
                    user_id=user.id,
                    host_name=settings.local.host.name,
                    server_name=self.server.name,
                    org_name=org.name,
                    user_name=user.name,
                    platform=platform,
                    client_ver=client_ver,
                    device_id=device_id,
                    device_name=device_name,
                    virtual_ip=virt_address,
                    virtual_ip6=virt_address6,
                    remote_ip=remote_ip,
                    mac_addr=mac_addr,
                    wg_public_key=wg_public_key,
                )
                host.global_clients.insert({
                    'instance_id': self.instance.id,
                    'client_id': client_id,
                })

            client_conf, network_links = self.generate_client_conf_wg(
                platform, client_id, virt_address, virt_address6, user)

            self.clients.update_id(client_id, {
                'network_links': network_links,
            })

            client_conf['address'] = virt_address
            if self.server.ipv6:
                client_conf['address6'] = virt_address6

            if self.server.debug:
                self.instance_com.push_output(
                    'Client wg conf %s:' % user_id)
                self.instance_com.push_output('  %s' % client_conf)

            self.instance.connect_wg(wg_public_key, virt_address,
                virt_address6, client_conf['network_links'],
                client_conf['network_links6'])

            self.connected(client_id)
        except:
            logger.exception('Error allowing client wg connect', 'server',
                server_id=self.server.id,
            )
            self.instance.disconnect_wg(wg_public_key, "allow_exception")
            return False, 'Error allowing client wg connect'

        addresses = set()
        if client_public_address:
            addresses.add(client_public_address)
        if client_public_address6:
            addresses.add(client_public_address6)
        addresses.add(remote_ip)

        if self.server.dynamic_firewall:
            firewall.open_client(self.instance.id, doc_id, list(addresses))

        return True, client_conf

    def decrypt_rsa(self, cipher_data):
        if len(cipher_data) > 1024:
            raise ValueError('Sender cipher data too long')

        cipher_data = base64.b64decode(cipher_data)

        plaintext = self.server_private_key.decrypt(
            cipher_data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA512()),
                algorithm=hashes.SHA512(),
                label=None,
            ),
        )

        data = json.loads(plaintext.decode())

        auth_password = data.get('password')
        auth_password = str(auth_password) if auth_password else None
        auth_token = utils.filter_str(data.get('token')) or None
        auth_nonce = utils.filter_str(data.get('nonce')) or None
        auth_timestamp = utils.filter_str(data.get('timestamp')) or None

        return auth_password, auth_token, auth_nonce, auth_timestamp

    def decrypt_box(self, sender_pub_key64, cipher_data64):
        if len(sender_pub_key64) > 128:
            raise ValueError('Sender pub key too long')

        if len(cipher_data64) > 256:
            raise ValueError('Sender cipher data too long')

        sender_pub_key64 += '=' * (-len(sender_pub_key64) % 4)
        cipher_data64 += '=' * (-len(cipher_data64) % 4)

        sender_pub_key = nacl.public.PublicKey(
            base64.b64decode(sender_pub_key64))

        pub_key_hash = hashlib.sha256(bytes(sender_pub_key)).digest()
        nonce = pub_key_hash[:24]
        auth_nonce = binascii.hexlify(pub_key_hash)

        priv_key = nacl.public.PrivateKey(
            base64.b64decode(self.server.auth_box_private_key))

        cipher_data = base64.b64decode(cipher_data64)

        nacl_box = nacl.public.Box(priv_key, sender_pub_key)

        plaintext = nacl_box.decrypt(cipher_data, nonce).decode()

        auth_token = plaintext[:16]
        auth_password = plaintext[26:]
        auth_timestamp = int(plaintext[16:26])

        return auth_password, auth_token, auth_nonce, auth_timestamp

    def decrypt_box_fw(self, sender_pub_key64, cipher_data64):
        if len(sender_pub_key64) > 128:
            raise ValueError('Sender pub key too long')

        if len(cipher_data64) > 256:
            raise ValueError('Sender cipher data too long')

        sender_pub_key64 += '=' * (-len(sender_pub_key64) % 4)
        cipher_data64 += '=' * (-len(cipher_data64) % 4)

        sender_pub_key = nacl.public.PublicKey(
            base64.b64decode(sender_pub_key64))

        pub_key_hash = hashlib.sha256(bytes(sender_pub_key)).digest()
        nonce = pub_key_hash[:24]

        priv_key = nacl.public.PrivateKey(
            base64.b64decode(self.server.auth_box_private_key))

        cipher_data = base64.b64decode(cipher_data64)

        nacl_box = nacl.public.Box(priv_key, sender_pub_key)

        plaintext = nacl_box.decrypt(cipher_data, nonce).decode()

        return plaintext

    def _connect(self, client_data, reauth):
        client_id = client_data['client_id']
        key_id = client_data['key_id']
        org_id = client_data['org_id']
        user_id = client_data['user_id']
        remote_ip = client_data.get('remote_ip')
        platform = client_data.get('platform')
        client_ver = client_data.get('client_ver')
        device_id = client_data.get('device_id')
        device_name = client_data.get('device_name')
        username = client_data.get('username')
        password = client_data.get('password')
        auth_password = None
        auth_token = None
        auth_nonce = None
        auth_timestamp = None
        mac_addr = client_data.get('mac_addr')
        has_token = False
        fw_token = None
        sso_token = None
        auth = None

        if password and password.startswith('$x$') and \
                len(username) > 24 and len(password) > 24 and \
                self.server_private_key:
            has_token = True
            auth_password, auth_token, auth_nonce, auth_timestamp = \
                self.decrypt_box(username, password[3:])
        elif password and password.startswith('$f$') and \
                len(username) > 24 and len(password) > 24 and \
                self.server_private_key:
            has_token = True
            fw_token = self.decrypt_box_fw(username, password[3:])
            if ':' in fw_token:
                tokens = fw_token.split(':')
                fw_token = tokens[0]
                sso_token = tokens[1]
        elif password and '<%=RSA_ENCRYPTED=%>' in password and \
                self.server_private_key:
            has_token = True
            auth_password, auth_token, auth_nonce, auth_timestamp = \
                self.decrypt_rsa(
                    password.split('<%=RSA_ENCRYPTED=%>', 1)[-1])
        elif password and '<%=PUSH_TOKEN=%>' in password:
            _, password = password.split('<%=PUSH_TOKEN=%>')
            password = password or None
        elif password and '<%=AUTH_TOKEN=%>' in password:
            _, password = password.split('<%=AUTH_TOKEN=%>')
            password = password or None

        try:
            if not _limiter.validate(remote_ip):
                self.instance_com.send_client_deny(client_id, key_id,
                    'Too many connect requests')
                return

            org = self.get_org(org_id)
            if not org:
                self.instance_com.send_client_deny(client_id, key_id,
                    'Organization is not valid')
                return

            user = org.get_user(user_id, fields=(
                '_id', 'name', 'email', 'pin', 'type', 'auth_type',
                'yubico_id', 'groups', 'last_active', 'disabled',
                'otp_secret', 'link_server_id', 'bypass_secondary',
                'client_to_client', 'mac_addresses', 'dns_servers',
                'dns_suffix', 'port_forwarding'))
            if not user:
                self.instance_com.send_client_deny(client_id, key_id,
                    'User is not valid')
                return

            def callback(allow, reason=None, doc_id=None):
                challenge = None
                if auth:
                    challenge = auth.challenge

                try:
                    if allow:
                        self.allow_client(client_data, org, user,
                            auth_password or password, reauth,
                            has_token, doc_id)
                    else:
                        self.instance_com.send_client_deny(
                            client_id, key_id, reason, challenge)

                    plugins.event(
                        'user_connection',
                        host_id=settings.local.host_id,
                        server_id=self.server.id,
                        org_id=org.id,
                        user_id=user.id,
                        host_name=settings.local.host.name,
                        server_name=self.server.name,
                        org_name=org.name,
                        user_name=user.name,
                        platform=platform,
                        device_id=device_id,
                        device_name=device_name,
                        remote_ip=remote_ip,
                        mac_addr=mac_addr,
                        password=password,
                        auth_password=auth_password,
                        auth_token=auth_token,
                        auth_nonce=auth_nonce,
                        auth_timestamp=auth_timestamp,
                        allow=allow,
                        reason=reason,
                    )
                except:
                    try:
                        self.instance_com.send_client_deny(
                            client_id, key_id, 'exception', challenge)
                    except:
                        pass

                    logger.exception(
                        'Error in authorizer callback', 'server',
                        server_id=self.server.id,
                        instance_id=self.instance.id,
                    )

            auth = authorizer.Authorizer(
                svr=self.server,
                usr=user,
                clients=self,
                mode='ovpn',
                stage='connect',
                remote_ip=remote_ip,
                platform=platform,
                client_ver=client_ver,
                device_id=device_id,
                device_name=device_name,
                mac_addr=mac_addr,
                mac_addrs=None,
                password=password,
                auth_password=auth_password,
                auth_token=auth_token,
                auth_nonce=auth_nonce,
                auth_timestamp=auth_timestamp,
                fw_token=fw_token,
                sso_token=sso_token,
                reauth=reauth,
                callback=callback,
            )

            auth.authenticate()
        except:
            logger.exception('Error parsing client connect', 'server',
                server_id=self.server.id,
            )
            self.instance_com.send_client_deny(client_id, key_id,
                'Error parsing client connect')

    def connect(self, client_data, reauth=False):
        self.call_queue.put(self._connect, client_data, reauth)

    def connect_wg(self, user, org, wg_public_key, auth_password,
            auth_token, auth_nonce, auth_timestamp, sso_token,
            platform, client_ver, device_id, device_name, mac_addr, mac_addrs,
            client_public_address, client_public_address6, remote_ip,
            connect_callback):
        response = {
            'sent': False,
            'lock': threading.Lock(),
        }

        if not self.instance.server.wg:
            raise TypeError('Server not wg')

        def connect_callback_once(allow, data):
            respond = False
            response['lock'].acquire()
            if not response['sent']:
                respond = True
            response['sent'] = True
            response['lock'].release()
            thread.cancel()

            if respond:
                connect_callback(allow, data)
                return True
            return False

        def timeout_callback():
            if connect_callback_once(False, 'Authorization timed out'):
                self.instance.disconnect_wg(wg_public_key, "authorize_timeout")

        thread = threading.Timer(30, timeout_callback)
        thread.daemon = True
        thread.start()

        try:
            def callback(allow, reason=None, doc_id=None):
                try:
                    if allow:
                        allow, data = self.allow_client_wg(
                            user=user,
                            org=org,
                            wg_public_key=wg_public_key,
                            platform=platform,
                            client_ver=client_ver,
                            device_id=device_id,
                            device_name=device_name,
                            password=auth_password,
                            mac_addr=mac_addr,
                            remote_ip=remote_ip,
                            client_public_address=client_public_address,
                            client_public_address6=client_public_address6,
                        )
                        if allow:
                            connect_callback_once(True, data)

                    if not allow:
                        self.instance_com.push_output(
                            'ERROR User auth wg failed "%s"' % reason)
                        connect_callback_once(False, reason)

                    plugins.event(
                        'user_connection',
                        host_id=settings.local.host_id,
                        server_id=self.server.id,
                        org_id=org.id,
                        user_id=user.id,
                        host_name=settings.local.host.name,
                        server_name=self.server.name,
                        org_name=org.name,
                        user_name=user.name,
                        platform=platform,
                        client_ver=client_ver,
                        device_id=device_id,
                        device_name=device_name,
                        remote_ip=remote_ip,
                        mac_addr=mac_addr,
                        password=None,
                        auth_password=auth_password,
                        auth_token=auth_token,
                        auth_nonce=auth_nonce,
                        auth_timestamp=auth_timestamp,
                        allow=allow,
                        reason=reason,
                        wg_public_key=wg_public_key,
                    )
                except:
                    self.instance.disconnect_wg(wg_public_key,
                        "authorize_exception")

                    try:
                        connect_callback_once(False, 'Server exception')
                    except:
                        pass

                    logger.exception(
                        'Error in authorizer callback', 'server',
                        server_id=self.server.id,
                        instance_id=self.instance.id,
                    )

            auth = authorizer.Authorizer(
                svr=self.server,
                usr=user,
                clients=self,
                mode='wg',
                stage='open',
                remote_ip=remote_ip,
                platform=platform,
                client_ver=client_ver,
                device_id=device_id,
                device_name=device_name,
                mac_addr=mac_addr,
                mac_addrs=mac_addrs,
                password=None,
                auth_password=auth_password,
                auth_token=auth_token,
                auth_nonce=auth_nonce,
                auth_timestamp=auth_timestamp,
                fw_token=None,
                sso_token=sso_token,
                reauth=False,
                callback=callback,
            )

            auth.authenticate()
        except:
            logger.exception('Error parsing client connect', 'server',
                server_id=self.server.id,
            )
            self.instance.disconnect_wg(wg_public_key, "connect_exception")
            connect_callback_once(False, 'Error parsing client connect')

    def open_firewall(self, user, client_public_address,
            client_public_address6, remote_ip):
        token = utils.generate_secret()
        doc_id = database.ObjectId()
        timestamp = utils.now()

        addresses = set()
        if client_public_address:
            addresses.add(client_public_address)
        if client_public_address6:
            addresses.add(client_public_address6)
        addresses.add(remote_ip)

        self.firewall_clients.insert({
            'doc_id': doc_id,
            'user_id': user.id,
            'token': token,
            'timestamp': timestamp,
            'addresses': list(addresses),
            'valid': True,
        })

        if self.server.dynamic_firewall:
            firewall.open_client(self.instance.id, doc_id, list(addresses))

        return token

    def open_ovpn(self, user, org, auth_password,
            auth_token, auth_nonce, auth_timestamp, sso_token, platform,
            client_ver, device_id, device_name, mac_addr, mac_addrs,
            client_public_address, client_public_address6, remote_ip,
            connect_callback):
        response = {
            'sent': False,
            'lock': threading.Lock(),
        }

        def connect_callback_once(allow, data):
            respond = False
            response['lock'].acquire()
            if not response['sent']:
                respond = True
            response['sent'] = True
            response['lock'].release()
            thread.cancel()

            if respond:
                connect_callback(allow, data)
                return True
            return False

        def timeout_callback():
            connect_callback_once(False, 'Authorization timed out')

        thread = threading.Timer(30, timeout_callback)
        thread.daemon = True
        thread.start()

        try:
            def callback(allow, reason=None, doc_id=None):
                try:
                    if allow:
                        token = self.open_firewall(
                            user,
                            client_public_address,
                            client_public_address6,
                            remote_ip,
                        )

                        if self.server.sso_auth:
                            conn_sso_token = utils.rand_str(32)

                            tokens_collection = mongo.get_collection(
                                'server_sso_tokens')
                            tokens_collection.insert_one({
                                '_id': conn_sso_token,
                                'user_id': user.id,
                                'server_id': self.server.id,
                                'stage': 'connect',
                                'timestamp': utils.now(),
                            })

                            connect_callback_once(True,
                                token + ":" + conn_sso_token)
                        else:
                            connect_callback_once(True, token)

                    if not allow:
                        self.instance_com.push_output(
                            'ERROR User open ovpn failed "%s"' % reason)
                        connect_callback_once(False, reason)

                    plugins.event(
                        'user_connection',
                        host_id=settings.local.host_id,
                        server_id=self.server.id,
                        org_id=org.id,
                        user_id=user.id,
                        host_name=settings.local.host.name,
                        server_name=self.server.name,
                        org_name=org.name,
                        user_name=user.name,
                        platform=platform,
                        client_ver=client_ver,
                        device_id=device_id,
                        device_name=device_name,
                        remote_ip=remote_ip,
                        mac_addr=mac_addr,
                        password=None,
                        auth_password=auth_password,
                        auth_token=auth_token,
                        auth_nonce=auth_nonce,
                        auth_timestamp=auth_timestamp,
                        allow=allow,
                        reason=reason,
                    )
                except:
                    try:
                        connect_callback_once(False, 'Server exception')
                    except:
                        pass

                    logger.exception(
                        'Error in authorizer callback', 'server',
                        server_id=self.server.id,
                        instance_id=self.instance.id,
                    )

            auth = authorizer.Authorizer(
                svr=self.server,
                usr=user,
                clients=self,
                mode='ovpn',
                stage='open',
                remote_ip=remote_ip,
                platform=platform,
                client_ver=client_ver,
                device_id=device_id,
                device_name=device_name,
                mac_addr=mac_addr,
                mac_addrs=mac_addrs,
                password=None,
                auth_password=auth_password,
                auth_token=auth_token,
                auth_nonce=auth_nonce,
                auth_timestamp=auth_timestamp,
                fw_token=None,
                sso_token=sso_token,
                reauth=False,
                callback=callback,
            )

            auth.authenticate()
        except:
            logger.exception('Error parsing client connect', 'server',
                server_id=self.server.id,
            )
            connect_callback_once(False, 'Error parsing client connect')

    def ping_wg(self, user, org, wg_public_key):
        updated = self.clients.update_id(wg_public_key, {
            'timestamp_wg': time.time(),
        })
        if not updated:
            return False
        return True

    def on_port_forwarding(self, org_id, user_id):
        client = self.clients.find({'user_id': user_id})
        if not client:
            return
        client = client[0]

        org = self.get_org(org_id)
        if not org:
            return

        usr = org.get_user(user_id, fields=(
            '_id', 'name', 'email', 'pin', 'type', 'auth_type',
            'disabled', 'otp_secret', 'link_server_id',
            'bypass_secondary', 'client_to_client', 'dns_servers',
            'dns_suffix', 'port_forwarding'))
        if not usr:
            return

        if len(client['id']) > 32:
            rules, rules6 = self.generate_iptables_rules_wg(
                usr,
                client['virt_address'],
                client['virt_address6'],
            )
        else:
            rules, rules6 = self.generate_iptables_rules(
                usr,
                client['virt_address'],
                client['virt_address6'],
            )

        self.clear_iptables_rules(
            client['iptables_rules'],
            client['ip6tables_rules'],
        )

        if not self.clients.update_id(client['id'], {
                    'iptables_rules': rules,
                    'ip6tables_rules': rules6,
                }):
            return

        self.set_iptables_rules(rules, rules6)

    def generate_iptables_rules(self, usr, virt_address, virt_address6):
        rules = []
        rules6 = []

        client_addr = virt_address.split('/')[0]
        client_addr6 = virt_address6.split('/')[0]

        if usr.client_to_client:
            for chain in ('INPUT', 'OUTPUT', 'FORWARD'):
                rules.append([
                    chain,
                    '-d', client_addr,
                    '-j', 'DROP',
                ])
                rules6.append([
                    chain,
                    '-d', client_addr6,
                    '-j', 'DROP',
                ])
                rules.append([
                    chain,
                    '-s', client_addr,
                    '-j', 'DROP',
                ])
                rules6.append([
                    chain,
                    '-s', client_addr6,
                    '-j', 'DROP',
                ])
                rules.append([
                    chain,
                    '-d', client_addr,
                    '-s', self.server.network,
                    '-j', 'ACCEPT',
                ])
                rules6.append([
                    chain,
                    '-d', client_addr6,
                    '-s', self.server.network6,
                    '-j', 'ACCEPT',
                ])
                rules.append([
                    chain,
                    '-s', client_addr,
                    '-d', self.server.network,
                    '-j', 'ACCEPT',
                ])
                rules6.append([
                    chain,
                    '-s', client_addr6,
                    '-d', self.server.network6,
                    '-j', 'ACCEPT',
                ])

        if not usr.port_forwarding:
            return rules, rules6

        forward_base_args = [
            'FORWARD',
            '-d', client_addr,
            '-o', self.instance.interface,
            '-j', 'ACCEPT',
        ]

        forward_base_args6 = [
            'FORWARD',
            '-d', client_addr6,
            '-o', self.instance.interface,
            '-j', 'ACCEPT',
        ]

        prerouting_base_args = [
            'PREROUTING',
            '-t', 'nat',
            '!', '-i', self.instance.interface,
            '-j', 'DNAT',
        ]

        output_base_args = [
            'OUTPUT',
            '-t', 'nat',
            '-o', 'lo',
            '-j', 'DNAT',
        ]

        extra_args = []

        forward2_base_rule = [
            'FORWARD',
            '-s', client_addr,
            '-i', self.instance.interface,
            '-m', 'conntrack',
            '--ctstate','RELATED,ESTABLISHED',
            '-j', 'ACCEPT',
        ] + extra_args
        rules.append(forward2_base_rule)
        if self.server.ipv6:
            forward2_base_rule6 = [
                'FORWARD',
                '-s', client_addr6,
                '-i', self.instance.interface,
                '-m', 'conntrack',
                '--ctstate','RELATED,ESTABLISHED',
                '-j', 'ACCEPT',
            ] + extra_args
            rules6.append(forward2_base_rule6)

        for data in usr.port_forwarding:
            proto = data.get('protocol')
            port = data['port']
            dport = data.get('dport')

            if not port:
                continue

            client_addr_port = client_addr
            client_addr_port6 = client_addr6
            if not dport:
                dport = port
                port = ''
            else:
                client_addr_port += ':' + port
                client_addr_port6 += ':' + port
            dport = dport.replace('-', ':')

            if proto:
                protos = [proto]
            else:
                protos = ['tcp', 'udp']

            for proto in protos:
                rule = prerouting_base_args + [
                    '-p', proto,
                    '-m', proto,
                    '--dport', dport,
                    '--to-destination', client_addr_port,
                ] + extra_args
                rules.append(rule)

                if self.server.ipv6:
                    rule = prerouting_base_args + [
                        '-p', proto,
                        '-m', proto,
                        '--dport', dport,
                        '--to-destination', client_addr_port6,
                    ] + extra_args
                    rules6.append(rule)


                rule = output_base_args + [
                    '-p', proto,
                    '-m', proto,
                    '--dport', dport,
                    '--to-destination', client_addr_port,
                ] + extra_args
                rules.append(rule)

                if self.server.ipv6:
                    rule = output_base_args + [
                        '-p', proto,
                        '-m', proto,
                        '--dport', dport,
                        '--to-destination', client_addr_port6,
                    ] + extra_args
                    rules6.append(rule)


                rule = forward_base_args + [
                    '-p', proto,
                    '-m', proto,
                    '--dport', port or dport,
                ] + extra_args
                rules.append(rule)
                if self.server.ipv6:
                    rule = forward_base_args6 + [
                        '-p', proto,
                        '-m', proto,
                        '--dport', port or dport,
                    ] + extra_args
                    rules6.append(rule)

        return rules, rules6

    def generate_iptables_rules_wg(self, usr, virt_address, virt_address6):
        rules = []
        rules6 = []

        client_addr = virt_address.split('/')[0]
        client_addr6 = virt_address6.split('/')[0]

        if not usr.port_forwarding:
            return rules, rules6

        forward_base_args = [
            'FORWARD',
            '-d', client_addr,
            '-o', self.instance.interface_wg,
            '-j', 'ACCEPT',
        ]

        forward_base_args6 = [
            'FORWARD',
            '-d', client_addr6,
            '-o', self.instance.interface_wg,
            '-j', 'ACCEPT',
        ]

        prerouting_base_args = [
            'PREROUTING',
            '-t', 'nat',
            '!', '-i', self.instance.interface_wg,
            '-j', 'DNAT',
        ]

        output_base_args = [
            'OUTPUT',
            '-t', 'nat',
            '-o', 'lo',
            '-j', 'DNAT',
        ]

        extra_args = []

        forward2_base_rule = [
            'FORWARD',
            '-s', client_addr,
            '-i', self.instance.interface_wg,
            '-m', 'conntrack',
            '--ctstate','RELATED,ESTABLISHED',
            '-j', 'ACCEPT',
        ] + extra_args
        rules.append(forward2_base_rule)
        if self.server.ipv6:
            forward2_base_rule6 = [
                'FORWARD',
                '-s', client_addr6,
                '-i', self.instance.interface_wg,
                '-m', 'conntrack',
                '--ctstate','RELATED,ESTABLISHED',
                '-j', 'ACCEPT',
            ] + extra_args
            rules6.append(forward2_base_rule6)

        for data in usr.port_forwarding:
            proto = data.get('protocol')
            port = data['port']
            dport = data.get('dport')

            if not port:
                continue

            client_addr_port = client_addr
            client_addr_port6 = client_addr6
            if not dport:
                dport = port
                port = ''
            else:
                client_addr_port += ':' + port
                client_addr_port6 += ':' + port
            dport = dport.replace('-', ':')

            if proto:
                protos = [proto]
            else:
                protos = ['tcp', 'udp']

            for proto in protos:
                rule = prerouting_base_args + [
                    '-p', proto,
                    '-m', proto,
                    '--dport', dport,
                    '--to-destination', client_addr_port,
                ] + extra_args
                rules.append(rule)

                if self.server.ipv6:
                    rule = prerouting_base_args + [
                        '-p', proto,
                        '-m', proto,
                        '--dport', dport,
                        '--to-destination', client_addr_port6,
                    ] + extra_args
                    rules6.append(rule)


                rule = output_base_args + [
                    '-p', proto,
                    '-m', proto,
                    '--dport', dport,
                    '--to-destination', client_addr_port,
                ] + extra_args
                rules.append(rule)

                if self.server.ipv6:
                    rule = output_base_args + [
                        '-p', proto,
                        '-m', proto,
                        '--dport', dport,
                        '--to-destination', client_addr_port6,
                    ] + extra_args
                    rules6.append(rule)


                rule = forward_base_args + [
                    '-p', proto,
                    '-m', proto,
                    '--dport', port or dport,
                ] + extra_args
                rules.append(rule)
                if self.server.ipv6:
                    rule = forward_base_args6 + [
                        '-p', proto,
                        '-m', proto,
                        '--dport', port or dport,
                    ] + extra_args
                    rules6.append(rule)

        return rules, rules6

    def set_iptables_rules(self, rules, rules6):
        if rules or rules6:
            self.instance.enable_iptables_tun_nat()
            for rule in rules:
                self.instance.iptables.add_rule(rule)
            for rule6 in rules6:
                self.instance.iptables.add_rule6(rule6)

    def clear_iptables_rules(self, rules, rules6):
        if rules or rules6:
            for rule in rules:
                self.instance.iptables.remove_rule(rule, silent=True)
            for rule6 in rules6:
                self.instance.iptables.remove_rule6(rule6, silent=True)

    def _connected(self, client_id):
        client = self.clients.find_id(client_id)
        if not client:
            self.instance_com.push_output(
                'ERROR Unknown client connected client_id=%s' % client_id)
            if len(client_id) > 32:
                self.instance.disconnect_wg(client_id, "unknown_client")
            else:
                self.instance_com.client_kill(client_id, "unknown_client")
            return

        journal.entry(
            journal.USER_CONNECT_NETWORK,
            self.server.journal_data,
            user_id=client['user_id'],
            user_name=client['user_name'],
            user_type=client['user_type'],
            platform=client['platform'],
            type=client['user_type'],
            device_name=client['device_name'],
            mac_addr=client['mac_addr'],
            real_address=client['real_address'],
            virt_address=client['virt_address'],
            virt_address6=client['virt_address6'],
            host_address=self.route_addr,
            host_address6=self.route_addr6,
            event_long='User connected to network',
        )

        self.set_iptables_rules(
            client['iptables_rules'],
            client['ip6tables_rules'],
        )

        timestamp = utils.now()
        doc = {
            '_id': client['doc_id'],
            'user_id': client['user_id'],
            'server_id': self.server.id,
            'host_id': settings.local.host_id,
            'ipv6': self.server.ipv6,
            'timestamp': timestamp,
            'platform': client['platform'],
            'type': client['user_type'],
            'device_name': client['device_name'],
            'mac_addr': client['mac_addr'],
            'network': self.server.network,
            'network_wg': self.server.network_wg,
            'network_links': client['network_links'],
            'real_address': client['real_address'],
            'virt_address': client['virt_address'],
            'virt_address6': client['virt_address6'],
            'host_address': self.route_addr,
            'host_address6': self.route_addr6,
            'dns_servers': client['dns_servers'],
            'dns_suffix': client['dns_suffix'],
            'connected_since': int(timestamp.strftime('%s')),
        }

        if client['type'] == 'wg':
            doc['wg_public_key'] = client.get('wg_public_key')

        if settings.local.sub_active and \
                settings.local.sub_plan and \
                'enterprise' in settings.local.sub_plan:
            domain_user = str(client['user_name']).split(
                '@')[0].lower().replace('.', '-')
            domain_org = str(client['org_name']).lower().replace('.', '-')
            domain = domain_user + '.' + domain_org
            domain_hash = utils.unsafe_md5()
            domain_hash.update(domain.encode())
            domain_hash = bson.binary.Binary(domain_hash.digest(),
                subtype=bson.binary.MD5_SUBTYPE)
            doc['domain'] = domain_hash
            doc['domain_name'] = domain
            doc['virt_address_num'] = utils.ip_to_long(
                client['virt_address'].split('/')[0])

        try:
            self.collection.insert_one(doc)
            if self.server.route_clients:
                messenger.publish('client', {
                    'state': True,
                    'server_id': self.server.id,
                    'virt_address': client['virt_address'],
                    'virt_address6': client['virt_address6'],
                    'host_address': self.route_addr,
                    'host_address6': self.route_addr6,
                })
                messenger.publish('client_links', {
                    'state': True,
                    'server_id': self.server.id,
                    'virt_address': client['virt_address'],
                    'virt_address6': client['virt_address6'],
                    'host_address': self.route_addr,
                    'host_address6': self.route_addr6,
                    'network_links': client['network_links'],
                })

        except:
            logger.exception('Error adding client', 'server',
                server_id=self.server.id,
            )
            if client['type'] == 'wg':
                self.instance.disconnect_wg(client_id, "client_db_err")
            else:
                self.instance_com.client_kill(client_id, "client_db_err")
            return

        self.clients.update_id(client_id, {
            'timestamp': time.time(),
        })

        self.clients_queue.append(client_id)
        self.auths_queue.append(client_id)

        if client['type'] == 'wg':
            self.instance_com.push_output(
                'User connected wg user_id=%s' % client['user_id'])
        else:
            self.instance_com.push_output(
                'User connected user_id=%s' % client['user_id'])
        self.send_event()

    def connected(self, client_id):
        self.call_queue.put(self._connected, client_id)

    def _disconnected(self, client):
        org_id = client['org_id']
        user_id = client['user_id']
        remote_ip = client['real_address']
        virt_address = client['virt_address']
        virt_address6 = client['virt_address6']

        org = self.get_org(org_id)
        if org:
            user = org.get_user(user_id)
        else:
            user = None

        if user:
            user.audit_event(
                'user_connection',
                'User disconnected from "%s"' % self.server.name,
                remote_addr=remote_ip,
                server_name=self.server.name,
            )
            journal.entry(
                journal.USER_DISCONNECT,
                user.journal_data,
                self.server.journal_data,
                remote_address=remote_ip,
                event_long='User disconnected',
            )
            monitoring.insert_point('user_disconnections', {
                'host': settings.local.host.name,
                'server': self.server.name,
            }, {
                'user': user.name,
                'remote_ip': remote_ip,
            })
            plugins.event(
                'user_disconnected',
                host_id=settings.local.host_id,
                server_id=self.server.id,
                org_id=org_id,
                user_id=user_id,
                host_name=settings.local.host.name,
                server_name=self.server.name,
                org_name=org.name,
                user_name=user.name,
                remote_ip=remote_ip,
                virtual_ip=virt_address,
                virtual_ip6=virt_address6,
            )
        else:
            journal.entry(
                journal.USER_DISCONNECT,
                {
                    'user_id': user_id,
                },
                self.server.journal_data,
                remote_address=remote_ip,
                event_long='User disconnected',
            )
            plugins.event(
                'user_disconnected',
                host_id=settings.local.host_id,
                server_id=self.server.id,
                org_id=org_id,
                user_id=user_id,
                host_name=settings.local.host.name,
                server_name=self.server.name,
                org_name='',
                user_name='',
                remote_ip=remote_ip,
                virtual_ip=virt_address,
                virtual_ip6=virt_address6,
            )

        # if self.server.route_clients and not client.get('ignore_routes'):
        #     messenger.publish('client', {
        #         'state': False,
        #         'server_id': self.server.id,
        #         'virt_address': client['virt_address'],
        #         'virt_address6': client['virt_address6'],
        #         'host_address': self.route_addr,
        #         'host_address6': settings.local.host.local_addr6,
        #     })
        #
        # if client['network_links']:
        #     messenger.publish('client_links', {
        #         'state': False,
        #         'server_id': self.server.id,
        #         'virt_address': client['virt_address'],
        #         'virt_address6': client['virt_address6'],
        #         'host_address': self.route_addr,
        #         'host_address6': settings.local.host.local_addr6,
        #         'network_links': client['network_links'],
        #     })

        self.instance_com.push_output(
            'User disconnected user_id=%s' % client['user_id'])
        self.send_event()

    def disconnected(self, client_id):
        client = self.clients.find_id(client_id)
        if not client:
            return

        self.clients.remove_id(client_id)
        host.global_clients.remove({
            'instance_id': self.instance.id,
            'client_id': client_id,
        })
        self.remove_iroutes(client_id)

        self.clear_iptables_rules(
            client['iptables_rules'],
            client['ip6tables_rules'],
        )

        doc_id = client.get('doc_id')
        if doc_id:
            try:
                self.collection.delete_one({
                    '_id': doc_id,
                })
            except:
                logger.exception('Error removing client', 'server',
                    server_id=self.server.id,
                )

        if self.server.multi_device:
            if client['address_dynamic']:
                self.pool_collection.update_one({
                    'server_id': self.server.id,
                    'user_id': client.get('user_id'),
                    'client_id': doc_id,
                }, {'$set': {
                    'user_id': None,
                    'mac_addr': None,
                    'client_id': None,
                    'timestamp': None,
                }})
            else:
                self.pool_collection.delete_many({
                    'server_id': self.server.id,
                    'user_id': client.get('user_id'),
                    'client_id': doc_id,
                })

        self.call_queue.put(self._disconnected, client)

    def disconnect_user(self, user_id):
        for client in self.clients.find({'user_id': user_id}):
            if len(client['id']) > 32:
                self.instance.disconnect_wg(client['id'], "disconnect")
            else:
                self.instance_com.client_kill(client['id'], "disconnect")

    def disconnect_user_id(self, user_id, client_id, server_id):
        if server_id and self.server.id != server_id:
            return

        for clnt in self.clients.find({'user_id': user_id}):
            if clnt.get('doc_id') == client_id:
                if len(clnt['id']) > 32:
                    self.instance.disconnect_wg(clnt['id'], "disconnect_id")
                else:
                    self.instance_com.client_kill(clnt['id'], "disconnect_id")

    def disconnect_user_mac(self, user_id, host_id, mac_addr, server_id):
        if host_id == settings.local.host_id:
            return

        if server_id and self.server.id != server_id:
            return

        for clnt in self.clients.find({
                    'user_id': user_id,
                    'mac_addr': mac_addr,
                }):
            if len(clnt['id']) > 32:
                self.instance.disconnect_wg(clnt['id'], "disconnect_mac")
            else:
                self.instance_com.client_kill(clnt['id'], "disconnect_mac")

    def reconnect_user(self, user_id, host_id, server_id):
        if host_id == settings.local.host_id:
            return

        if server_id and self.server.id != server_id:
            return

        for client in self.clients.find({'user_id': user_id}):
            self.clients.update_id(client['id'], {
                'ignore_routes': True,
            })
            if len(client['id']) > 32:
                self.instance.disconnect_wg(client['id'], "reconnect")
            else:
                self.instance_com.client_kill(client['id'], "reconnect")

    def send_event(self):
        for org_id in self.server.organizations:
            event.Event(
                type=USERS_UPDATED,
                resource_id=org_id,
                delay=SERVER_EVENT_DELAY,
            )
        event.Event(
            type=HOSTS_UPDATED,
            resource_id=settings.local.host_id,
            delay=SERVER_EVENT_DELAY,
        )
        event.Event(
            type=SERVERS_UPDATED,
            delay=SERVER_EVENT_DELAY,
        )

    def interrupter_sleep(self, length):
        if check_global_interrupt() or self.instance.sock_interrupt:
            return True
        while True:
            sleep = min(0.5, length)
            time.sleep(sleep)
            length -= sleep
            if check_global_interrupt() or self.instance.sock_interrupt:
                return True
            elif length <= 0:
                return False

    @interrupter
    def iroute_ping_thread(self, client_id, virt_address):
        thread_id = uuid.uuid4().hex
        self.iroutes_thread[client_id] = thread_id

        yield interrupter_sleep(6)

        while True:
            yield interrupter_sleep(self.server.link_ping_interval)

            if client_id not in self.iroutes_index or \
                    self.iroutes_thread.get(client_id) != thread_id:
                break

            if not self.has_failover_iroute(client_id):
                continue

            latency = utils.ping(virt_address,
                timeout=self.server.link_ping_timeout)
            if latency is None and self.has_failover_iroute(client_id):
                self.instance_com.push_output(
                    'Gateway link timeout on %s' % virt_address)
                if len(client_id) > 32:
                    self.instance.disconnect_wg(client_id, "link_ping_err")
                else:
                    self.instance_com.client_kill(client_id, "link_ping_err")
                break

    def _auth_check(self, client):
        if not settings.app.sso_connection_check:
            return

        client_id = client['id']

        org = self.get_org(client['org_id'])
        if org:
            usr = org.get_user(client['user_id'])
        else:
            usr = None

        if not usr:
            logger.error('User lost unexpectedly',
                'server',
                server_id=self.server.id,
                instance_id=self.instance.id,
                user_id=client['user_id'],
            )
            if len(client_id) > 32:
                self.instance.disconnect_wg(client_id, "auth_lost_err")
            else:
                self.instance_com.client_kill(client_id, "auth_lost_err")
            return

        if usr.bypass_secondary or settings.vpn.stress_test:
            return

        if not usr.sso_auth_check(self.server, client['password'],
                client['real_address'], True):
            time.sleep(0.3)
            if not usr.sso_auth_check(self.server, client['password'],
                    client['real_address'], True):
                logger.error('User failed auth update check',
                    'server',
                    server_id=self.server.id,
                    instance_id=self.instance.id,
                    user_id=client['user_id'],
                )
                if len(client_id) > 32:
                    self.instance.disconnect_wg(client_id, "auth_update_err")
                else:
                    self.instance_com.client_kill(client_id, "auth_update_err")
                return

        if not self.server.check_groups(usr.groups) and \
                usr.type != CERT_SERVER:
            logger.error('User failed auth group update check',
                'server',
                server_id=self.server.id,
                instance_id=self.instance.id,
                user_id=client['user_id'],
            )
            if len(client_id) > 32:
                self.instance.disconnect_wg(client_id, "auth_group_err")
            else:
                self.instance_com.client_kill(client_id, "auth_group_err")
            return

    @interrupter
    def auth_thread(self):
        while True:
            try:
                try:
                    client_id = self.auths_queue.popleft()
                except IndexError:
                    if self.interrupter_sleep(10):
                        return
                    continue

                client = self.clients.find_id(client_id)
                if not client:
                    continue

                diff = settings.app.sso_connection_check_ttl - \
                        (time.time() - client['auth_check_timestamp'])

                if diff > settings.app.sso_connection_check_ttl:
                    logger.error('Client auth time diff out of range',
                        'server',
                        time_diff=diff,
                        server_id=self.server.id,
                        instance_id=self.instance.id,
                    )
                    if self.interrupter_sleep(10):
                        return
                elif diff > 1:
                    if self.interrupter_sleep(diff):
                        return

                if self.instance.sock_interrupt:
                    return

                client = self.clients.find_id(client_id)
                if not client:
                    continue

                self.clients.update_id(client['id'], {
                    'auth_check_timestamp': time.time(),
                })

                try:
                    self._auth_check(client)
                except:
                    logger.exception('Failed to update client',
                        'server',
                        server_id=self.server.id,
                        instance_id=self.instance.id,
                    )
                    yield interrupter_sleep(1)
                    continue
                finally:
                    self.auths_queue.append(client_id)

                yield
                if self.instance.sock_interrupt:
                    return
            except GeneratorExit:
                raise
            except:
                logger.exception('Error in auth thread', 'server',
                    server_id=self.server.id,
                    instance_id=self.instance.id,
                )
                yield interrupter_sleep(3)
                if self.instance.sock_interrupt:
                    return
                time.sleep(1)

    @interrupter
    def ping_thread(self):
        try:
            while True:
                try:
                    try:
                        client_id = self.clients_queue.popleft()
                    except IndexError:
                        if self.interrupter_sleep(10):
                            return
                        continue

                    client = self.clients.find_id(client_id)
                    if not client:
                        continue

                    diff = int(settings.vpn.client_ttl / 2) - \
                           (time.time() - client['timestamp'])

                    if diff > settings.vpn.client_ttl:
                        logger.error('Client ping time diff out of range',
                            'server',
                            time_diff=diff,
                            server_id=self.server.id,
                            instance_id=self.instance.id,
                        )
                        if self.interrupter_sleep(10):
                            return
                    elif diff > 1:
                        if self.interrupter_sleep(diff):
                            return

                    client = self.clients.find_id(client_id)
                    if not client:
                        continue

                    if self.instance.sock_interrupt:
                        return

                    if self.server.session_timeout and \
                            time.time() - client['timestamp_start'] > \
                            self.server.session_timeout:
                        self.instance_com.push_output(
                            'Client session timeout ' +
                            'user_id=%s' % client['user_id'])
                        if len(client_id) > 32:
                            self.instance.disconnect_wg(client_id,
                                "session_limit")
                        else:
                            self.instance_com.client_kill(client_id,
                                "session_limit")

                    try:
                        updated = self.clients.update_id(client_id, {
                            'timestamp': time.time(),
                        })
                        if not updated:
                            continue

                        if client['type'] == 'wg' and \
                                time.time() - client['timestamp_wg'] > \
                                self.server.ping_timeout_wg:
                            self.instance.disconnect_wg(client_id,
                                "ping_timeout")
                            continue

                        response = self.collection.update_one({
                            '_id': client['doc_id'],
                        }, {'$set': {
                            'timestamp': utils.now(),
                            'real_address': client['real_address'],
                        }})
                        if not bool(response.modified_count):
                            logger.error('Client lost unexpectedly',
                                'server',
                                server_id=self.server.id,
                                instance_id=self.instance.id,
                                client_id=client['doc_id'],
                            )
                            if len(client_id) > 32:
                                self.instance.disconnect_wg(client_id,
                                    "ping_lost_err")
                            else:
                                self.instance_com.client_kill(client_id,
                                    "ping_lost_err")
                            continue

                        if self.server.multi_device:
                            response = self.pool_collection.update_one({
                                'client_id': client['doc_id'],
                            }, {'$set': {
                                'timestamp': utils.now(),
                            }})

                            if not bool(response.modified_count):
                                logger.error('Client pool lost unexpectedly',
                                    'server',
                                    server_id=self.server.id,
                                    instance_id=self.instance.id,
                                    client_id=client['doc_id'],
                                )
                                if len(client_id) > 32:
                                    self.instance.disconnect_wg(client_id,
                                        "ping_pool_err")
                                else:
                                    self.instance_com.client_kill(client_id,
                                        "ping_pool_err")
                                continue
                    except:
                        self.clients_queue.append(client_id)
                        logger.exception('Failed to update client',
                            'server',
                            server_id=self.server.id,
                            instance_id=self.instance.id,
                        )
                        yield interrupter_sleep(1)
                        continue

                    self.clients_queue.append(client_id)

                    yield
                    if self.instance.sock_interrupt:
                        return
                except GeneratorExit:
                    raise
                except:
                    logger.exception('Error in client thread', 'server',
                        server_id=self.server.id,
                        instance_id=self.instance.id,
                    )
                    yield interrupter_sleep(3)
                    if self.instance.sock_interrupt:
                        return
        finally:
            doc_ids = []
            for client in self.clients.find_all():
                doc_id = client.get('doc_id')
                if doc_id:
                    doc_ids.append(doc_id)

            try:
                self.collection.delete_one({
                    '_id': {'$in': doc_ids},
                })
            except:
                logger.exception('Error removing client', 'server',
                    server_id=self.server.id,
                )

    def on_client(self, state, server_id, virt_address, virt_address6,
            host_address, host_address6):
        if server_id != self.server.id:
            return

        if state:
            self.clients_call_queue.put(self.add_route, virt_address,
                virt_address6, host_address, host_address6)
        else:
            self.clients_call_queue.put(self.remove_route, virt_address,
                virt_address6, host_address, host_address6)

    def on_client_link(self, state, server_id, virt_address, virt_address6,
            host_address, host_address6, network_links):
        if server_id != self.server.id:
            return

        if not host_address or \
                host_address == settings.local.host.local_addr or \
                host_address == self.route_addr:
            return

        if state:
            self.clients_call_queue.put(self.add_links_route, virt_address,
                virt_address6, host_address, host_address6, network_links)
        else:
            self.clients_call_queue.put(self.remove_links_route,
                virt_address, virt_address6, host_address, host_address6,
                network_links)

    def init_routes(self):
        for doc in self.collection.find({
                    'server_id': self.server.id,
                    'type': CERT_CLIENT,
                }):
            if doc['host_id'] == settings.local.host_id:
                continue

            virt_address = doc.get('virt_address')
            virt_address6 = doc.get('virt_address6')
            host_address = doc.get('host_address')
            host_address6 = doc.get('host_address6')
            network_links = doc.get('network_links')

            if not virt_address or not host_address:
                continue

            if self.instance.is_interrupted():
                return

            self.add_route(virt_address, virt_address6,
                host_address, host_address6)

            if network_links:
                for network_link in network_links:
                    self.add_link_route(network_link,
                        host_address, host_address6)

        self.clients_call_queue.start()

    def clear_routes(self):
        for virt_address in self.client_routes.copy():
            self.remove_route(virt_address, None, None, None)

        for virt_address6 in self.client_routes6.copy():
            self.remove_route(None, virt_address6, None, None)

        for network_link in self.link_routes.copy():
            self.remove_route(network_link, None, None, None)

        for network_link6 in self.link_routes6.copy():
            self.remove_route(None, network_link6, None, None)

    def add_route(self, virt_address, virt_address6,
            host_address, host_address6):
        if virt_address:
            virt_address = virt_address.split('/')[0]

            try:
                if virt_address in self.client_routes:
                    try:
                        self.client_routes.remove(virt_address)
                    except KeyError:
                        pass
                    utils.del_route(virt_address)

                if not host_address or \
                        host_address == settings.local.host.local_addr or \
                        host_address == self.route_addr:
                    return

                self.client_routes.add(virt_address)
                utils.add_route(virt_address, host_address)
            except:
                logger.exception('Failed to add route', 'clients',
                    virt_address=virt_address,
                    virt_address6=virt_address6,
                    host_address=host_address,
                    host_address6=host_address6,
                )

        if self.server.ipv6 and virt_address6:
            virt_address6 = virt_address6.split('/')[0]

            try:
                if virt_address6 in self.client_routes6:
                    try:
                        self.client_routes6.remove(virt_address6)
                    except KeyError:
                        pass
                    utils.del_route6(virt_address6)

                if not host_address6 or \
                        host_address6 == settings.local.host.local_addr6 or \
                        host_address6 == self.route_addr6:
                    return

                self.client_routes6.add(virt_address6)
                utils.add_route6(virt_address6, host_address6)
            except:
                logger.exception('Failed to add route6', 'clients',
                    virt_address=virt_address,
                    virt_address6=virt_address6,
                    host_address=host_address,
                    host_address6=host_address6,
                )

    def remove_route(self, virt_address, virt_address6,
            host_address, host_address6):
        if virt_address:
            virt_address = virt_address.split('/')[0]

            try:
                self.client_routes.remove(virt_address)
            except KeyError:
                pass

            utils.del_route(virt_address)

        if virt_address6:
            virt_address6 = virt_address6.split('/')[0]

            try:
                self.client_routes6.remove(virt_address6)
            except KeyError:
                pass

            utils.del_route6(virt_address6)

    def add_link_route(self, network_link, host_address, host_address6):
        try:
            if ':' in network_link:
                if network_link in self.link_routes6:
                    try:
                        self.link_routes6.remove(network_link)
                    except KeyError:
                        pass
                    utils.del_route(network_link)

                self.link_routes6.add(network_link)
                utils.add_route6(
                    network_link,
                    host_address6.split('/')[0],
                )
            else:
                if network_link in self.link_routes6:
                    try:
                        self.link_routes.remove(network_link)
                    except KeyError:
                        pass
                    utils.del_route(network_link)

                self.link_routes.add(network_link)
                utils.add_route(
                    network_link,
                    host_address.split('/')[0],
                )
        except:
            logger.exception('Failed to add link route', 'clients',
                network_link=network_link,
                host_address=host_address,
                host_address6=host_address6,
            )

    def remove_link_route(self, network_link, host_address, host_address6):
        if ':' in network_link:
            try:
                self.link_routes6.remove(network_link)
            except KeyError:
                pass

            utils.del_route(network_link)
        else:
            try:
                self.link_routes.remove(network_link)
            except KeyError:
                pass

            utils.del_route(network_link)

    def add_links_route(self, virt_address, virt_address6,
            host_address, host_address6, network_links):
        for network_link in network_links:
            self.add_link_route(network_link, host_address, host_address6)

    def remove_links_route(self, virt_address, virt_address6,
            host_address, host_address6, network_links):
        pass
        # for network_link in network_links:
        #     self.remove_link_route(network_link,
        #         host_address, host_address6)

    def on_firewall(self, client_id):
        clients = self.clients.find({
            'doc_id': client_id,
        })
        if clients:
            return True
        clients = self.firewall_clients.find({
            'doc_id': client_id,
        })
        if clients:
            client = clients[0]
            if utils.now() - client['timestamp'] < datetime.timedelta(
                    seconds=settings.vpn.firewall_connect_timeout):
                return True
            else:
                self.firewall_clients.remove_id(client['id'])
        return False

    def start(self):
        callbacks.add_port_listener(
            self.instance.id, self.on_port_forwarding)
        callbacks.add_client_listener(
            self.instance.id, self.on_client)
        callbacks.add_client_link_listener(
            self.instance.id, self.on_client_link)
        callbacks.add_firewall_listener(
            self.instance.id, self.on_firewall)
        host.global_servers.add(self.instance.id)

        if self.server.dns_mapping:
            host.dns_mapping_servers.add(self.instance.id)
        self.call_queue.start(settings.vpn.call_queue_threads)

        if self.server.route_clients:
            thread = threading.Thread(name="InitRoutes", target=self.init_routes)
            thread.daemon = True
            thread.start()

    def stop(self):
        callbacks.remove_port_listener(self.instance.id)
        callbacks.remove_client_listener(self.instance.id)
        callbacks.remove_client_link_listener(self.instance.id)
        callbacks.remove_firewall_listener(self.instance.id)

        try:
            host.global_servers.remove(self.instance.id)
        except KeyError:
            pass

        try:
            host.dns_mapping_servers.remove(self.instance.id)
        except KeyError:
            pass

        host.global_clients.remove({
            'instance_id': self.instance.id,
        })

        if self.server.route_clients:
            self.clear_routes()
