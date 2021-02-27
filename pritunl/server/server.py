from pritunl.server.output import ServerOutput
from pritunl.server.output_link import ServerOutputLink
from pritunl.server.bandwidth import ServerBandwidth
from pritunl.server.ip_pool import ServerIpPool
from pritunl.server.instance import ServerInstance

from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *
from pritunl import settings
from pritunl import logger
from pritunl import host
from pritunl import utils
from pritunl import mongo
from pritunl import queue
from pritunl import transaction
from pritunl import event
from pritunl import messenger
from pritunl import organization
from pritunl import ipaddress
from pritunl import journal

import os
import subprocess
import random
import collections
import datetime
import base64
import nacl.utils
import nacl.public
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

dict_fields = [
    'id',
    'name',
    'status',
    'start_timestamp',
    'uptime',
    'instances',
    'organizations',
    'groups',
    'wg',
    'ipv6',
    'ipv6_firewall',
    'network',
    'network_wg',
    'network_mode',
    'network_start',
    'network_end',
    'restrict_routes',
    'bind_address',
    'port',
    'protocol',
    'port_wg',
    'dh_param_bits',
    'dh_params',
    'multi_device',
    'dns_servers',
    'search_domain',
    'otp_auth',
    'cipher',
    'hash',
    'block_outside_dns',
    'jumbo_frames',
    'lzo_compression',
    'inter_client',
    'ping_interval',
    'ping_timeout',
    'ping_timeout_wg',
    'link_ping_interval',
    'link_ping_timeout',
    'inactive_timeout',
    'session_timeout',
    'allowed_devices',
    'max_clients',
    'max_devices',
    'replica_count',
    'vxlan',
    'dns_mapping',
    'debug',
    'pre_connect_msg',
    'mss_fix',
    'auth_public_key',
    'auth_private_key',
    'auth_box_public_key',
    'auth_box_private_key',
]
operation_fields = dict_fields + [
    'hosts',
    'links',
    'replica_count',
    'tls_auth_key',
    'ca_certificate',
]

class Server(mongo.MongoObject):
    fields = {
        'name',
        'network',
        'network_lock',
        'network_lock_ttl',
        'network_wg',
        'bind_address',
        'port',
        'protocol',
        'port_wg',
        'dh_param_bits',
        'wg',
        'ipv6',
        'ipv6_firewall',
        'network_mode',
        'network_start',
        'network_end',
        'restrict_routes',
        'multi_device',
        'routes',
        'dns_servers',
        'search_domain',
        'otp_auth',
        'tls_auth',
        'tls_auth_key',
        'lzo_compression',
        'inter_client',
        'ping_interval',
        'ping_timeout',
        'ping_timeout_wg',
        'link_ping_interval',
        'link_ping_timeout',
        'inactive_timeout',
        'session_timeout',
        'dns_mapping',
        'debug',
        'pre_connect_msg',
        'mss_fix',
        'cipher',
        'hash',
        'block_outside_dns',
        'jumbo_frames',
        'organizations',
        'groups',
        'hosts',
        'links',
        'primary_organization',
        'primary_user',
        'ca_certificate',
        'dh_params',
        'status',
        'start_timestamp',
        'allowed_devices',
        'max_clients',
        'max_devices',
        'replica_count',
        'vxlan',
        'instances',
        'instances_count',
        'availability_group',
        'auth_public_key',
        'auth_private_key',
        'auth_box_public_key',
        'auth_box_private_key',
    }
    fields_default = {
        'wg': False,
        'ipv6': False,
        'ipv6_firewall': True,
        'network_mode': TUNNEL,
        'multi_device': False,
        'routes': [
            {
                'network': '0.0.0.0/0',
                'nat': True,
            },
        ],
        'dns_servers': [],
        'otp_auth': False,
        'tls_auth': True,
        'lzo_compression': False,
        'restrict_routes': True,
        'inter_client': True,
        'ping_interval': 10,
        'ping_timeout': 60,
        'ping_timeout_wg': 360,
        'link_ping_interval': 1,
        'link_ping_timeout': 5,
        'debug': False,
        'cipher': 'aes256',
        'hash': 'sha1',
        'block_outside_dns': False,
        'jumbo_frames': False,
        'organizations': [],
        'hosts': [],
        'links': [],
        'status': OFFLINE,
        'max_clients': 2000,
        'replica_count': 1,
        'vxlan': True,
        'instances': [],
        'instances_count': 0,
    }
    cache_prefix = 'server'

    def __init__(self, name=None, groups=None, network_wg=None,
            network=None, network_mode=None, network_start=None,
            network_end=None, restrict_routes=None, wg=None, ipv6=None,
            ipv6_firewall=None, bind_address=None, port=None,
            protocol=None, port_wg=None, dh_param_bits=None,
            multi_device=None, dns_servers=None, search_domain=None,
            otp_auth=None, cipher=None, hash=None, block_outside_dns=None,
            jumbo_frames=None, lzo_compression=None, inter_client=None,
            ping_interval=None, ping_timeout=None, ping_timeout_wg=None,
            link_ping_interval=None, link_ping_timeout=None,
            inactive_timeout=None, session_timeout=None,
            allowed_devices=None, max_clients=None, max_devices=None,
            replica_count=None, vxlan=None, dns_mapping=None, debug=None,
            pre_connect_msg=None, mss_fix=None, **kwargs):
        mongo.MongoObject.__init__(self)

        if 'network' in self.loaded_fields:
            self._orig_network = self.network
            self._orig_network_start = self.network_start
            self._orig_network_end = self.network_end
            self._orig_network_hash = self.network_hash
        self._orgs_added = []
        self._orgs_removed = []

        if name is not None:
            self.name = name
        if groups is not None:
            self.groups = groups
        if network is not None:
            self.network = network
        if network_wg is not None:
            self.network_wg = network_wg
        if network_mode is not None:
            self.network_mode = network_mode
        if network_start is not None:
            self.network_start = network_start
        if network_end is not None:
            self.network_end = network_end
        if restrict_routes is not None:
            self.restrict_routes = restrict_routes
        if wg is not None:
            self.wg = wg
        if ipv6 is not None:
            self.ipv6 = ipv6
        if ipv6_firewall is not None:
            self.ipv6_firewall = ipv6_firewall
        if bind_address is not None:
            self.bind_address = bind_address
        if port is not None:
            self.port = port
        if protocol is not None:
            self.protocol = protocol
        if port_wg is not None:
            self.port_wg = port_wg
        if dh_param_bits is not None:
            self.dh_param_bits = dh_param_bits
        if multi_device is not None:
            self.multi_device = multi_device
        if dns_servers is not None:
            self.dns_servers = dns_servers
        if search_domain is not None:
            self.search_domain = search_domain
        if otp_auth is not None:
            self.otp_auth = otp_auth
        if cipher is not None:
            self.cipher = cipher
        if hash is not None:
            self.hash = hash
        if block_outside_dns is not None:
            self.block_outside_dns = block_outside_dns
        if jumbo_frames is not None:
            self.jumbo_frames = jumbo_frames
        if lzo_compression is not None:
            self.lzo_compression = lzo_compression
        if inter_client is not None:
            self.inter_client = inter_client
        if ping_interval is not None:
            self.ping_interval = ping_interval
        if ping_timeout is not None:
            self.ping_timeout = ping_timeout
        if ping_timeout_wg is not None:
            self.ping_timeout_wg = ping_timeout_wg
        if link_ping_interval is not None:
            self.link_ping_interval = link_ping_interval
        if link_ping_timeout is not None:
            self.link_ping_timeout = link_ping_timeout
        if inactive_timeout is not None:
            self.inactive_timeout = inactive_timeout
        if session_timeout is not None:
            self.session_timeout = session_timeout
        if allowed_devices is not None:
            self.allowed_devices = allowed_devices
        if max_clients is not None:
            self.max_clients = max_clients
        if max_devices is not None:
            self.max_devices = max_devices
        if replica_count is not None:
            self.replica_count = replica_count
        if vxlan is not None:
            self.vxlan = vxlan
        if dns_mapping is not None:
            self.dns_mapping = dns_mapping
        if debug is not None:
            self.debug = debug
        if pre_connect_msg is not None:
            self.pre_connect_msg = pre_connect_msg
        if mss_fix is not None:
            self.mss_fix = mss_fix

    @cached_static_property
    def collection(cls):
        return mongo.get_collection('servers')

    @cached_static_property
    def host_collection(cls):
        return mongo.get_collection('hosts')

    @cached_static_property
    def vxlan_collection(cls):
        return mongo.get_collection('vxlans')

    @cached_static_property
    def user_collection(cls):
        return mongo.get_collection('users')

    @cached_static_property
    def user_net_link_collection(cls):
        return mongo.get_collection('users_net_link')

    @cached_static_property
    def clients_collection(cls):
        return mongo.get_collection('clients')

    @cached_static_property
    def clients_pool_collection(cls):
        return mongo.get_collection('clients_pool')

    @cached_static_property
    def org_collection(cls):
        return mongo.get_collection('organizations')

    @property
    def journal_data(self):
        return {
            'server_id': self.id,
            'server_name': self.name,
            'server_network': self.network,
            'server_port': self.port,
        }

    def dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'status': PENDING if not self.dh_params else self.status,
            'uptime': self.uptime,
            'users_online': self.users_online,
            'devices_online': self.devices_online,
            'user_count': self.user_count,
            'network': self.network,
            'network_wg': self.network_wg,
            'bind_address': self.bind_address,
            'port': self.port,
            'port_wg': self.port_wg,
            'protocol': self.protocol,
            'dh_param_bits': self.dh_param_bits,
            'groups': self.groups or [],
            'wg': True if self.wg else False,
            'ipv6': True if self.ipv6 else False,
            'ipv6_firewall': True if self.ipv6_firewall else False,
            'network_mode': self.network_mode,
            'network_start': self.network_start,
            'network_end': self.network_end,
            'restrict_routes': self.restrict_routes,
            'multi_device': self.multi_device,
            'dns_servers': self.dns_servers,
            'search_domain': self.search_domain,
            'otp_auth': True if self.otp_auth else False,
            'cipher': self.cipher,
            'hash': self.hash,
            'block_outside_dns': self.block_outside_dns,
            'jumbo_frames': self.jumbo_frames,
            'lzo_compression': self.lzo_compression,
            'inter_client': True if self.inter_client else False,
            'ping_interval': self.ping_interval,
            'ping_timeout': self.ping_timeout,
            'ping_timeout_wg': self.ping_timeout_wg,
            'link_ping_interval': self.link_ping_interval,
            'link_ping_timeout': self.link_ping_timeout,
            'inactive_timeout': self.inactive_timeout,
            'session_timeout': self.session_timeout,
            'allowed_devices': self.allowed_devices,
            'max_clients': self.max_clients,
            'max_devices': self.max_devices,
            'replica_count': self.replica_count,
            'vxlan': self.vxlan,
            'dns_mapping': True if self.dns_mapping else False,
            'debug': True if self.debug else False,
            'pre_connect_msg': self.pre_connect_msg,
            'mss_fix': self.mss_fix,
        }

    @property
    def route_clients(self):
        return self.replica_count and self.replica_count > 1 \
            and self.inter_client and self.network_mode != BRIDGE

    @property
    def replicating(self):
        return self.replica_count and self.replica_count > 1 \
            and self.network_mode != BRIDGE

    @property
    def uptime(self):
        if self.status != ONLINE or not self.start_timestamp:
            return
        return max(int((
            utils.now() - self.start_timestamp).total_seconds()), 1)

    @property
    def network_hash(self):
        return utils.fnv32a(
            (self.network or '') + '-' +
            (self.network_start or '') + '-' +
            (self.network_end or '')
        )

    @property
    def network6(self):
        routed_subnet6 = settings.local.host.routed_subnet6
        if routed_subnet6:
            return utils.net4to6x96(routed_subnet6, self.network)
        return utils.net4to6x64(settings.vpn.ipv6_prefix, self.network)

    @property
    def network6_wg(self):
        routed_subnet6_wg = settings.local.host.routed_subnet6_wg
        if routed_subnet6_wg:
            return utils.net4to6x96(routed_subnet6_wg, self.network)
        return utils.net4to6x64(settings.vpn.ipv6_prefix_wg, self.network)

    def ip4to4wg(self, addr):
        addr = ipaddress.ip_network(addr, strict=False)
        wg_net = ipaddress.ip_network(self.network_wg, strict=False)
        addr_bin = bin(int(
            wg_net.network_address))[2:].zfill(32)[:addr.prefixlen] + \
            bin(int(addr.network_address))[2:].zfill(32)[addr.prefixlen:]
        return utils.long_to_ip(int(addr_bin, 2)) + '/%d' % addr.prefixlen

    def ip4to6(self, addr):
        routed_subnet6 = settings.local.host.routed_subnet6
        if routed_subnet6:
            return utils.ip4to6x96(routed_subnet6, self.network, addr)
        return utils.ip4to6x64(settings.vpn.ipv6_prefix,
            self.network, addr)

    def ip4to6wg(self, addr):
        routed_subnet6 = settings.local.host.routed_subnet6_wg
        if routed_subnet6:
            return utils.ip4to6x96(routed_subnet6, self.network, addr)
        return utils.ip4to6x64(
            settings.vpn.ipv6_prefix_wg, self.network, addr)

    @cached_property
    def users_online(self):
        if self.status != ONLINE:
            return 0

        return len(self.clients_collection.distinct("user_id", {
            'server_id': self.id,
            'type': CERT_CLIENT,
        }))

    @cached_property
    def devices_online(self):
        if self.status != ONLINE:
            return 0

        return self.clients_collection.find({
            'server_id': self.id,
            'type': CERT_CLIENT,
        }).count()

    @cached_property
    def user_count(self):
        return organization.get_user_count_multi(org_ids=self.organizations)

    @cached_property
    def bandwidth(self):
        return ServerBandwidth(self.id)

    @cached_property
    def ip_pool(self):
        return ServerIpPool(self)

    @cached_property
    def output(self):
        return ServerOutput(self.id)

    @cached_property
    def output_link(self):
        return ServerOutputLink(self.id)

    @cached_property
    def network_links(self):
        links = set()
        users_links = collections.defaultdict(set)

        org_ids = self.org_collection.find({
            '_id': {'$in': self.organizations},
        }, {
            '_id': True,
        }).distinct('_id')

        for doc in self.user_net_link_collection.find({
                    'org_id': {'$in': org_ids},
                }):
            users_links[doc['user_id']].add(doc['network'])

        user_ids = self.user_collection.find({
            '_id': {'$in': list(users_links.keys())},
        }, {
            '_id': True,
        }).distinct('_id')

        for user_id in user_ids:
            links |= users_links[user_id]

        return links

    @property
    def adapter_type(self):
        return 'tap' if self.network_mode == BRIDGE else 'tun'

    @property
    def ca_certificate_x509(self):
        ca_split = self.ca_certificate.split('-----BEGIN CERTIFICATE-----')
        certs = []

        for cert in ca_split:
            if not cert:
                continue
            certs.append(cert.replace('-----END CERTIFICATE-----',
                '').replace('\n', ''))

        return certs

    def initialize(self):
        self.generate_tls_auth_start()
        try:
            self.generate_dh_param()
        finally:
            self.generate_tls_auth_wait()

    def generate_auth_key(self):
        if self.auth_public_key and self.auth_private_key and \
                self.auth_box_public_key and self.auth_box_private_key:
            return False

        if not self.auth_public_key or not self.auth_private_key:
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=4096,
                backend=default_backend(),
            )

            private_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            )

            public_pem = private_key.public_key().public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.PKCS1,
            )

            self.auth_public_key = public_pem.decode()
            self.auth_private_key = private_pem.decode()

        if not self.auth_box_public_key or not self.auth_box_private_key:
            priv_key = nacl.public.PrivateKey.generate()

            self.auth_box_public_key = base64.b64encode(
                bytes(priv_key.public_key)).decode()
            self.auth_box_private_key = base64.b64encode(
                bytes(priv_key)).decode()

        return True

    def generate_auth_key_commit(self):
        if self.generate_auth_key():
            self.commit({
                'auth_public_key', 'auth_private_key',
                'auth_box_public_key', 'auth_box_private_key',
            })

    def get_auth_private_key(self):
        self.generate_auth_key_commit()

        private_key = serialization.load_pem_private_key(
            self.auth_private_key.encode(),
            password=None,
            backend=default_backend(),
        )

        return private_key

    def queue_dh_params(self, block=False):
        queue.start('dh_params', block=block, server_id=self.id,
            dh_param_bits=self.dh_param_bits, priority=HIGH)
        self.dh_params = None

        if block:
            self.load()

    def is_route_all(self):
        for route in self.get_routes():
            if route['network'] == '0.0.0.0/0':
                return True
        return False

    def get_routes(self, include_hidden=False, include_default=True,
            include_server_links=False):
        routes = []
        link_routes = []
        routes_dict = {}
        virtual_comment = None
        virtual_metric = None
        virtual_advertise = None
        virtual_vpc_region = None
        virtual_vpc_id = None

        for network_link in self.network_links:
            route_id = network_link.encode().hex()
            routes_dict[network_link] = ({
                'id': route_id,
                'server': self.id,
                'network': network_link,
                'comment': None,
                'metric': 0,
                'nat': False,
                'nat_interface': None,
                'nat_netmap': None,
                'advertise': None,
                'vpc_region': None,
                'vpc_id': None,
                'net_gateway': False,
                'virtual_network': False,
                'network_link': True,
                'server_link': False,
                'link_virtual_network': False,
            })

        if include_server_links:
            for link_svr in self.iter_links(fields=('_id', 'wg',
                   'network', 'network_wg', 'network_start',
                   'network_end', 'routes', 'organizations', 'links',
                   'ipv6')):
                for route in link_svr.get_routes():
                    if route['network'] == '0.0.0.0/0':
                        continue

                    data = routes_dict.get(route['network'], {})

                    data['id'] = route['id']
                    data['server'] = self.id
                    data['network'] = route['network']
                    data['comment'] = route.get('comment')
                    data['metric'] = route.get('metric')
                    data['nat'] = route['nat']
                    data['nat_interface'] = route['nat_interface']
                    data['nat_netmap'] = route['nat_netmap']
                    data['advertise'] = None
                    data['vpc_region'] = None
                    data['vpc_id'] = None
                    data['net_gateway'] = route['net_gateway']
                    data['virtual_network'] = False
                    data['network_link'] = False
                    data['server_link'] = True
                    data['link_virtual_network'] = route['virtual_network']

                    routes_dict[route['network']] = data

        for route in self.routes:
            route_network = route['network']
            route_id = route_network.encode().hex()

            if route_network == '0.0.0.0/0':
                if not include_default:
                    continue

                routes.append({
                    'id': route_id,
                    'server': self.id,
                    'network': route_network,
                    'comment': route.get('comment'),
                    'metric': route.get('metric'),
                    'nat': route.get('nat', True),
                    'nat_interface': route.get('nat_interface'),
                    'nat_netmap': route.get('nat_netmap'),
                    'advertise': route.get('advertise', None),
                    'vpc_region': route.get('vpc_region', None),
                    'vpc_id': route.get('vpc_id', None),
                    'net_gateway': route.get('net_gateway', False),
                    'virtual_network': False,
                    'network_link': False,
                    'server_link': False,
                    'link_virtual_network': False,
                })

                if include_hidden and self.ipv6:
                    routes.append({
                        'id': '::/0'.encode().hex(),
                        'server': self.id,
                        'network': '::/0',
                        'comment': route.get('comment'),
                        'metric': route.get('metric'),
                        'nat': route.get('nat', True),
                        'nat_interface': route.get('nat_interface'),
                        'nat_netmap': route.get('nat_netmap'),
                        'advertise': route.get('advertise'),
                        'vpc_region': route.get('vpc_region'),
                        'vpc_id': route.get('vpc_id'),
                        'net_gateway': route.get('net_gateway', False),
                        'virtual_network': False,
                        'network_link': False,
                        'server_link': False,
                        'link_virtual_network': False,
                    })
            elif route_network == 'virtual':
                virtual_comment = route.get('comment', None)
                virtual_metric = route.get('metric', None)
                virtual_advertise = route.get('advertise', None)
                virtual_vpc_region = route.get('vpc_region', None)
                virtual_vpc_id = route.get('vpc_id', None)
            elif route_network == self.network or \
                    route_network == self.network6:
                continue
            elif route_network == self.network_wg or \
                    route_network == self.network6_wg:
                continue
            else:
                if route_network in routes_dict:
                    if not route.get('server_link'):
                        routes_dict[route_network]['nat'] = route.get(
                            'nat', True)
                        routes_dict[route_network]['nat_interface'] = \
                            route.get('nat_interface')
                        routes_dict[route_network]['nat_netmap'] = \
                            route.get('nat_netmap')
                    routes_dict[route_network]['comment'] = route.get(
                        'comment')
                    routes_dict[route_network]['metric'] = route.get(
                        'metric')
                    routes_dict[route_network]['advertise'] = route.get(
                        'advertise')
                    routes_dict[route_network]['vpc_region'] = route.get(
                        'vpc_region')
                    routes_dict[route_network]['vpc_id'] = route.get(
                        'vpc_id')
                else:
                    if route.get('server_link') and \
                            route_network not in routes_dict:
                        continue

                    routes_dict[route_network] = {
                        'id': route_id,
                        'server': self.id,
                        'network': route_network,
                        'comment': route.get('comment'),
                        'metric': route.get('metric'),
                        'nat': route.get('nat', True),
                        'nat_interface': route.get('nat_interface'),
                        'nat_netmap': route.get('nat_netmap'),
                        'advertise': route.get('advertise', None),
                        'vpc_region': route.get('vpc_region', None),
                        'vpc_id': route.get('vpc_id', None),
                        'net_gateway': route.get('net_gateway', False),
                        'virtual_network': False,
                        'network_link': False,
                        'server_link': False,
                        'link_virtual_network': False,
                    }

        routes.append({
            'id': self.network.encode().hex(),
            'server': self.id,
            'network': self.network,
            'comment': virtual_comment,
            'metric': virtual_metric,
            'nat': False,
            'nat_interface': None,
            'nat_netmap': None,
            'advertise': virtual_advertise,
            'vpc_region': virtual_vpc_region,
            'vpc_id': virtual_vpc_id,
            'net_gateway': False,
            'virtual_network': True,
            'network_link': False,
            'server_link': False,
            'link_virtual_network': False,
        })

        if self.wg:
            routes.append({
                'id': self.network_wg.encode().hex(),
                'server': self.id,
                'network': self.network_wg,
                'comment': virtual_comment,
                'metric': virtual_metric,
                'nat': False,
                'nat_interface': None,
                'nat_netmap': None,
                'advertise': virtual_advertise,
                'vpc_region': virtual_vpc_region,
                'vpc_id': virtual_vpc_id,
                'net_gateway': False,
                'virtual_network': True,
                'wg_network': True,
                'network_link': False,
                'server_link': False,
                'link_virtual_network': False,
            })

        if self.ipv6:
            routes.append({
                'id': self.network6.encode().hex(),
                'server': self.id,
                'network': self.network6,
                'comment': virtual_comment,
                'metric': virtual_metric,
                'nat': False,
                'nat_interface': None,
                'nat_netmap': None,
                'advertise': virtual_advertise,
                'vpc_region': virtual_vpc_region,
                'vpc_id': virtual_vpc_id,
                'net_gateway': False,
                'virtual_network': True,
                'network_link': False,
                'server_link': False,
                'link_virtual_network': False,
            })

            if self.wg:
                routes.append({
                    'id': self.network6_wg.encode().hex(),
                    'server': self.id,
                    'network': self.network6_wg,
                    'comment': virtual_comment,
                    'metric': virtual_metric,
                    'nat': False,
                    'nat_interface': None,
                    'nat_netmap': None,
                    'advertise': virtual_advertise,
                    'vpc_region': virtual_vpc_region,
                    'vpc_id': virtual_vpc_id,
                    'net_gateway': False,
                    'virtual_network': True,
                    'wg_network': True,
                    'network_link': False,
                    'server_link': False,
                    'link_virtual_network': False,
                })

        for route_network in sorted(routes_dict.keys()):
            if not routes_dict[route_network]['server_link']:
                routes.append(routes_dict[route_network])
            elif not routes_dict[route_network]['virtual_network']:
                link_routes.append(routes_dict[route_network])

        return routes + link_routes

    def upsert_route(self, network, nat_route, nat_interface, nat_netmap,
            advertise, vpc_region, vpc_id, net_gateway, comment, metric):
        exists = False

        if self.status == ONLINE:
            raise ServerOnlineError(
                'Cannot add route while server is online')

        try:
            network = str(ipaddress.ip_network(network))
        except ValueError:
            raise NetworkInvalid('Network address is invalid')

        orig_network = network

        server_link = False
        for route in self.get_routes(include_server_links=True):
            if route['network'] == network:
                server_link = route['server_link']
                if server_link and route['nat'] != nat_route:
                    raise ServerRouteNatServerLink('Cannot nat server link')

                if route['network_link'] and net_gateway:
                    raise ServerRouteGatewayNetworkLink(
                        'Cannot use network gateway with network link')

        if network == self.network or network == self.network6:
            network = 'virtual'

            if nat_route:
                raise ServerRouteNatVirtual('Cannot nat virtual network')
        elif network == '::/0':
            network = '0.0.0.0/0'

        if net_gateway and nat_route:
            raise ServerRouteNatNetGateway('Cannot nat net gateway')

        if not nat_route and nat_netmap:
            raise ServerRouteNonNatNetmap('Cannot use netmap without nat')

        for route in self.routes:
            if route['network'] == network:
                if not server_link:
                    route['nat'] = nat_route
                    route['nat_interface'] = nat_interface
                    route['nat_netmap'] = nat_netmap
                route['comment'] = comment
                route['metric'] = metric
                route['advertise'] = advertise
                route['vpc_region'] = vpc_region
                route['vpc_id'] = vpc_id
                route['net_gateway'] = net_gateway
                route['server_link'] = server_link
                exists = True
                break

        if not exists:
            self.routes.append({
                'network': network,
                'comment': comment,
                'metric': metric,
                'nat': nat_route,
                'nat_interface': nat_interface,
                'nat_netmap': nat_netmap,
                'advertise': advertise,
                'vpc_region': vpc_region,
                'vpc_id': vpc_id,
                'net_gateway': net_gateway,
                'server_link': server_link,
            })

        return {
            'id': orig_network.encode().hex(),
            'server': self.id,
            'network': orig_network,
            'comment': comment,
            'metric': metric,
            'nat': nat_route,
            'nat_interface': nat_interface,
            'nat_netmap': nat_netmap,
            'advertise': advertise,
            'vpc_region': vpc_region,
            'vpc_id': vpc_id,
            'net_gateway': net_gateway,
        }

    def remove_route(self, network):
        if self.status == ONLINE:
            raise ServerOnlineError(
                'Cannot remove route while server is online')

        for i, route in enumerate(self.routes):
            if route['network'] == network:
                self.routes.pop(i)
                break

    def has_non_nat_route(self):
        for route in self.get_routes(include_default=False):
            if route['virtual_network'] or route['network_link'] or \
                    route['server_link'] or route['net_gateway']:
                continue

            if not route['nat']:
                return True

        return False

    def check_groups(self, groups):
        if not self.groups:
            return True
        if not groups:
            return False
        return bool(set(groups) & set(self.groups))

    def get_link_server(self, link_server_id, fields=None):
        return Server(id=link_server_id, fields=fields)

    def get_cache_key(self, suffix=None):
        if not self.cache_prefix:
            raise AttributeError('Cached config object requires cache_prefix')

        key = self.cache_prefix + '-' + self.id
        if suffix:
            key += '-%s' % suffix

        return key

    def get_ip_addr(self, org_id, user_id):
        return self.ip_pool.get_ip_addr(org_id, user_id)

    def assign_ip_addr(self, org_id, user_id):
        if not self.network_lock:
            self.ip_pool.assign_ip_addr(org_id, user_id)
        else:
            queue.start('assign_ip_addr', server_id=self.id, org_id=org_id,
                user_id=user_id)

    def unassign_ip_addr(self, org_id, user_id):
        if not self.network_lock:
            self.ip_pool.unassign_ip_addr(org_id, user_id)
        else:
            queue.start('unassign_ip_addr', server_id=self.id, org_id=org_id,
                user_id=user_id)

    def get_sync_remotes(self):
        remotes = set()
        spec = {
            '_id': {'$in': self.hosts},
        }
        project = {
            '_id': False,
            'public_address': True,
            'auto_public_address': True,
            'auto_public_host': True,
            'sync_address': True,
        }

        for doc in self.host_collection.find(spec, project):
            sync_address = doc.get('sync_address')
            if sync_address:
                remotes.add('https://%s' % sync_address)
            else:
                address = doc.get('auto_public_host') or \
                    doc['public_address'] or \
                    doc['auto_public_address']
                if settings.app.server_port == 443:
                    remotes.add('https://%s' % address)
                else:
                    remotes.add('https://%s:%s' % (
                        address,
                        settings.app.server_port,
                    ))

        remotes = list(remotes)
        remotes.sort()

        return remotes

    def get_key_remotes(self, include_link_addr=False):
        remotes = set()
        remotes6 = set()
        spec = {
            '_id': {'$in': self.hosts},
        }
        project = {
            '_id': False,
            'public_address': True,
            'auto_public_address': True,
            'auto_public_host': True,
            'public_address6': True,
            'auto_public_address6': True,
            'auto_public_host6': True,
        }

        if include_link_addr:
            project['link_address'] = True

        if self.protocol == 'tcp':
            protocol = 'tcp-client'
            protocol6 = 'tcp6-client'
        elif self.protocol == 'udp':
            protocol = 'udp'
            protocol6 = 'udp6'
        else:
            raise ValueError('Unknown protocol')

        for doc in self.host_collection.find(spec, project):
            if include_link_addr and doc['link_address']:
                address = doc['link_address']
                if ':' in address and settings.vpn.ipv6:
                    remotes6.add('remote %s %s %s' % (
                        address, self.port, protocol6))
                else:
                    remotes.add('remote %s %s %s' % (
                        doc['link_address'], self.port, protocol))
            else:
                address = doc.get('auto_public_host') or \
                    doc['public_address'] or doc['auto_public_address']
                remotes.add('remote %s %s %s' % (
                    address, self.port, protocol))

                address6 = doc.get('auto_public_host6') or \
                    doc.get('public_address6') or \
                    doc.get('auto_public_address6')
                if address6 and settings.vpn.ipv6:
                    remotes6.add('remote %s %s %s' % (
                        address6, self.port, protocol6))

        remotes = list(remotes)
        remotes6 = list(remotes6)
        random.shuffle(remotes)
        random.shuffle(remotes6)

        if self.ipv6 or settings.vpn.ipv6:
            remotes = remotes6 + remotes

        if len(remotes) > 1:
            remotes.append('remote-random')

        return '\n'.join(remotes)

    def get_hosts(self):
        hosts = []
        spec = {
            '_id': {'$in': self.hosts},
        }
        project = {
            '_id': False,
            'public_address': True,
            'auto_public_address': True,
            'auto_public_host': True,
            'public_address6': True,
            'auto_public_address6': True,
            'auto_public_host6': True,
        }

        for doc in self.host_collection.find(spec, project):
            address = doc.get('auto_public_host') or \
                doc['public_address'] or doc['auto_public_address']
            hosts.append((address, self.port))

        random.shuffle(hosts)

        return hosts

    def commit(self, *args, **kwargs):
        tran = None

        if 'network' in self.loaded_fields and \
                self.network_hash != self._orig_network_hash:
            tran = transaction.Transaction()
            if self.network_lock:
                raise ServerNetworkLocked('Server network is locked', {
                    'server_id': self.id,
                    'lock_id': self.network_lock,
                })
            else:
                queue_ip_pool = queue.start('assign_ip_pool',
                    transaction=tran,
                    server_id=self.id,
                    network=self.network,
                    network_start=self.network_start,
                    network_end=self.network_end,
                    network_hash=self.network_hash,
                    old_network=self._orig_network,
                    old_network_start=self._orig_network_start,
                    old_network_end=self._orig_network_end,
                    old_network_hash=self._orig_network_hash,
                )
                self.network_lock = queue_ip_pool.id
                self.network_lock_ttl = utils.now() + \
                    datetime.timedelta(minutes=6)
        else:
            for org_id in self._orgs_added:
                self.ip_pool.assign_ip_pool_org(org_id)

            for org_id in self._orgs_removed:
                self.ip_pool.unassign_ip_pool_org(org_id)

        mongo.MongoObject.commit(self, transaction=tran, *args, **kwargs)

        if tran:
            messenger.publish('queue', 'queue_updated',
                transaction=tran)
            tran.commit()

    def remove(self):
        link_ids = []
        for link in self.links:
            link_ids.append(link.get('server_id'))

        spec = {
            '_id': {'$in': link_ids},
        }
        project = {
            '_id': True,
            'status': True,
        }

        for doc in self.collection.find(spec, project):
            if doc['status'] == ONLINE:
                raise ServerLinkOnlineError(
                    'Linked servers must be offline to unlink')

        for link in self.links:
            self.collection.update({
                '_id': link.get('server_id'),
            }, {'$pull': {
                'links': {'server_id': self.id},
            }})

        queue.stop(spec={
            'type': 'dh_params',
            'server_id': self.id,
        })
        self.remove_primary_user()

        mongo.MongoObject.remove(self)

        return link_ids

    def iter_links(self, fields=None):
        from pritunl.server.utils import iter_servers

        if not len(self.links):
            return

        spec = {
            '_id': {'$in': [x['server_id'] for x in self.links]},
        }
        for svr in iter_servers(spec=spec, fields=fields):
            yield svr

    def create_primary_user(self):
        try:
            org = next(self.iter_orgs())
        except StopIteration:
            self.stop()
            raise ServerMissingOrg('Primary user cannot be created ' + \
                'without any organizations', {
                    'server_id': self.id,
                })

        usr = org.new_user(name=SERVER_USER_PREFIX + str(self.id),
            type=CERT_SERVER, resource_id=self.id)
        usr.audit_event('user_created', 'User created for server')

        journal.entry(
            journal.USER_CREATE,
            usr.journal_data,
            self.journal_data,
            event_long='Server user created',
        )

        self.primary_organization = org.id
        self.primary_user = usr.id
        self.commit(('primary_organization', 'primary_user'))

    def remove_primary_user(self):
        self.user_collection.remove({
            'resource_id': self.id,
        })

        self.primary_organization = None
        self.primary_user = None

    def add_org(self, org_id):
        if not isinstance(org_id, str):
            org_id = org_id.id

        if org_id in self.organizations:
            return

        self.organizations.append(org_id)
        self.changed.add('organizations')
        self.generate_ca_cert()
        self._orgs_added.append(org_id)

    def remove_org(self, org_id):
        if not isinstance(org_id, str):
            org_id = org_id.id

        if org_id not in self.organizations:
            return

        if self.primary_organization == org_id:
            self.remove_primary_user()

        try:
            self.organizations.remove(org_id)
        except ValueError:
            pass

        self.changed.add('organizations')
        self.generate_ca_cert()
        self._orgs_removed.append(org_id)

    def iter_orgs(self, fields=None):
        spec = {
            '_id': {'$in': self.organizations},
        }
        for org in organization.iter_orgs(spec=spec, fields=fields):
            yield org

    def get_org(self, org_id, fields=None):
        if org_id in self.organizations:
            return organization.get_by_id(org_id, fields=fields)

    def get_org_fields(self, fields=None):
        project = {}
        push = {}

        for field in fields:
            if field == 'id':
                project['_id'] = True
                push[field] = '$_id'
            else:
                project[field] = True
                push[field] = '$' + field

        response = self.org_collection.aggregate([
            {'$match': {
                '_id': {'$in': self.organizations},
            }},
            {'$project': project},
            {'$group': {
                '_id': None,
                'orgs': {'$push': push},
            }},
        ])

        val = None
        for val in response:
            break

        if val:
            docs = val['orgs']
        else:
            docs = []

        return docs

    def add_host(self, host_id):
        if host_id in self.hosts:
            return

        if self.links:
            hosts_set = set(self.hosts)
            hosts_set.add(host_id)

            spec = {
            '_id': {'$in': [x['server_id'] for x in self.links]},
            }
            project = {
                '_id': True,
                'hosts': True,
            }

            for doc in self.collection.find(spec, project):
                if hosts_set & set(doc['hosts']):
                    raise ServerLinkCommonHostError(
                        'Servers have a common host')

        self.hosts.append(host_id)
        self.changed.add('hosts')

    def remove_host(self, host_id):
        if host_id not in self.hosts:
            logger.warning('Attempted to remove host that does not exists',
                'server',
                server_id=self.id,
                host_id=host_id,
            )
            return

        self.hosts.remove(host_id)

        response = self.collection.update({
            '_id': self.id,
            'instances.host_id': host_id,
        }, {
            '$pull': {
                'hosts': host_id,
                'instances': {
                    'host_id': host_id,
                },
            },
            '$inc': {
                'instances_count': -1,
            },
        })

        if response['updatedExisting']:
            self.publish('start', extra={
                'prefered_hosts': host.get_prefered_hosts(
                    self.hosts, self.replica_count),
            })

        doc = self.collection.find_and_modify({
            '_id': self.id,
        }, {'$pull': {
            'hosts': host_id,
        }}, fields={
            'hosts': True,
        }, new=True)

        if doc and not doc['hosts']:
            self.status = OFFLINE
            self.commit('status')

    def iter_hosts(self, fields=None):
        spec = {
            '_id': {'$in': self.hosts}
        }
        for hst in host.iter_hosts(spec=spec, fields=fields):
            yield hst

    def get_by_id(self, host_id):
        if host_id in self.hosts:
            return host.get_by_id(host_id)

    def generate_dh_param(self):
        doc = queue.find({
            'type': 'dh_params',
            'server_id': self.id,
        })
        if doc:
            if doc['dh_param_bits'] != self.dh_param_bits:
                queue.stop(doc['_id'])
            else:
                return

        reserved = queue.reserve('pooled_dh_params', svr=self)
        if not reserved:
            reserved = queue.reserve('queued_dh_params', svr=self)

        if reserved:
            queue.start('dh_params', dh_param_bits=self.dh_param_bits,
                priority=LOW)
            return

        self.queue_dh_params()

    def generate_tls_auth_start(self):
        self.tls_auth_temp_path = utils.get_temp_path()
        self.tls_auth_path = os.path.join(
            self.tls_auth_temp_path, TLS_AUTH_NAME)

        os.makedirs(self.tls_auth_temp_path)
        args = [
            'openvpn', '--genkey',
            '--secret', self.tls_auth_path,
        ]
        try:
            self.tls_auth_process = subprocess.Popen(args,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except:
            utils.rmtree(self.tls_auth_temp_path)
            raise

    def generate_tls_auth_wait(self):
        try:
            return_code = self.tls_auth_process.wait()
            if return_code:
                raise ValueError('Popen returned ' +
                    'error exit code %r' % return_code)
            self.read_file('tls_auth_key', self.tls_auth_path)
        finally:
            utils.rmtree(self.tls_auth_temp_path)

    def generate_tls_auth(self):
        self.generate_tls_auth_start()
        self.generate_tls_auth_wait()

    def generate_ca_cert(self):
        ca_certificate = ''
        for org in self.iter_orgs():
            ca_certificate += utils.get_cert_block(org.ca_certificate) + '\n'
        self.ca_certificate = ca_certificate.rstrip('\n')

    def get_cursor_id(self):
        return messenger.get_cursor_id('servers')

    def publish(self, message, transaction=None, extra=None):
        extra = extra or {}
        extra.update({
            'server_id': self.id,
        })
        messenger.publish('servers', message,
            extra=extra, transaction=transaction)

    def subscribe(self, cursor_id=None, timeout=None):
        for msg in messenger.subscribe('servers', cursor_id=cursor_id,
                timeout=timeout):
            if msg.get('server_id') == self.id:
                yield msg

    def send_link_events(self):
        event.Event(type=SERVER_LINKS_UPDATED, resource_id=self.id)
        for link in self.links:
            event.Event(type=SERVER_LINKS_UPDATED,
                resource_id=link['server_id'])

    def pre_start_check(self):
        if not self.tls_auth_key:
            self.generate_tls_auth()
            self.commit('tls_auth_key')

        if not self.ca_certificate:
            self.generate_ca_cert()
            self.commit('ca_certificate')

    def run(self, send_events=False):
        if settings.local.vpn_state == DISABLED:
            logger.warning(
                'VPN server disabled',
                'server',
                message=settings.local.notification,
            )
            return

        self.pre_start_check()
        instance = ServerInstance(self)
        instance.run(send_events=send_events)

    def get_best_availability_group(self):
        docs = self.host_collection.find({
            'status': ONLINE,
        }, {
            '_id': True,
            'availability_group': True,
        })

        hosts_group = {}
        for doc in docs:
            hosts_group[doc['_id']] = doc.get(
                'availability_group', DEFAULT)

        hosts_set = set(self.hosts)
        group_best = None
        group_len_max = 0
        server_groups = collections.defaultdict(set)

        for hst in hosts_set:
            avail_zone = hosts_group.get(hst)
            if not avail_zone:
                continue

            server_groups[avail_zone].add(hst)
            group_len = len(server_groups[avail_zone])

            if group_len > group_len_max:
                group_len_max = group_len
                group_best = avail_zone

        return group_best

    def start(self, timeout=None):
        timeout = timeout or settings.vpn.op_timeout
        cursor_id = self.get_cursor_id()

        if self.status != OFFLINE:
            return

        if not self.dh_params:
            self.generate_dh_param()
            return

        if not self.organizations:
            raise ServerMissingOrg('Server cannot be started ' + \
                'without any organizations', {
                    'server_id': self.id,
                })

        self.pre_start_check()

        start_timestamp = utils.now()
        response = self.collection.update({
            '_id': self.id,
            'status': OFFLINE,
            'instances_count': 0,
        }, {'$set': {
            'status': ONLINE,
            'pool_cursor': None,
            'start_timestamp': start_timestamp,
            'availability_group': self.get_best_availability_group(),
        }})

        if not response['updatedExisting']:
            raise ServerInstanceSet('Server instances already running. %r', {
                    'server_id': self.id,
                })

        self.clients_pool_collection.remove({
            'server_id': self.id,
        })

        self.status = ONLINE
        self.start_timestamp = start_timestamp

        replica_count = min(self.replica_count, len(self.hosts))

        started_count = 0
        error_count = 0
        try:
            self.publish('start', extra={
                'prefered_hosts': host.get_prefered_hosts(
                    self.hosts, replica_count),
            })

            for x_timeout in (4, timeout):
                for msg in self.subscribe(cursor_id=cursor_id,
                        timeout=x_timeout):
                    message = msg['message']
                    if message == 'started':
                        started_count += 1
                        if started_count + error_count >= replica_count:
                            break
                    elif message == 'error':
                        error_count += 1
                        if started_count + error_count >= replica_count:
                            break

                if started_count:
                    break

            if not started_count:
                if error_count:
                    raise ServerStartError('Server failed to start', {
                        'server_id': self.id,
                    })
                else:
                    raise ServerStartError('Server start timed out', {
                        'server_id': self.id,
                    })
        except:
            self.publish('force_stop')
            self.collection.update({
                '_id': self.id,
            }, {'$set': {
                'status': OFFLINE,
                'instances': [],
                'instances_count': 0,
            }})
            self.status = OFFLINE
            self.instances = []
            self.instances_count = 0
            raise

    def stop(self, force=False):
        if self.status != ONLINE:
            return

        response = self.collection.update({
            '_id': self.id,
            'status': ONLINE,
        }, {'$set': {
            'status': OFFLINE,
            'start_timestamp': None,
            'pool_cursor': None,
            'instances': [],
            'instances_count': 0,
            'availability_group': None,
        }})

        self.vxlan_collection.update({
            'server_id': self.id,
        }, {'$set': {
            'hosts': [],
        }})

        self.clients_pool_collection.remove({
            'server_id': self.id,
        })

        if not response['updatedExisting']:
            raise ServerStopError('Server not running', {
                    'server_id': self.id,
                })
        self.status = OFFLINE

        if force:
            self.publish('force_stop')
        else:
            self.publish('stop')

    def force_stop(self):
        self.stop(force=True)

    def restart(self):
        if self.status != ONLINE:
            self.start()
            return
        self.stop()
        self.start()

    def validate_conf(self, used_resources=None, allow_online=False):
        from pritunl.server.utils import get_used_resources

        if not used_resources:
            used_resources = get_used_resources(self.id)
        network_used = used_resources['networks']
        port_used = used_resources['ports']

        if self.status == ONLINE and not allow_online:
            return SERVER_NOT_OFFLINE, SERVER_NOT_OFFLINE_SETTINGS_MSG

        hosts = set()
        routes = set()
        for link_svr in self.iter_links():
            hosts_set = set(link_svr.hosts)
            if hosts & hosts_set:
                return SERVER_LINK_COMMON_HOST, SERVER_LINK_COMMON_HOST_MSG
            hosts.update(hosts_set)

            routes_set = set()
            for route in link_svr.get_routes():
                if route['network'] != '0.0.0.0/0':
                    routes_set.add(route['network'])
            if routes & routes_set:
                return SERVER_LINK_COMMON_ROUTE, SERVER_LINK_COMMON_ROUTE_MSG
            routes.update(routes_set)

            if link_svr.status == ONLINE and not allow_online:
                return SERVER_LINKS_NOT_OFFLINE, \
                    SERVER_LINKS_NOT_OFFLINE_SETTINGS_MSG

        if utils.check_network_overlap(self.network, network_used):
            return NETWORK_IN_USE, NETWORK_IN_USE_MSG

        network_used.add(ipaddress.ip_network(self.network))

        if self.wg and utils.check_network_overlap(
                self.network_wg, network_used):
            return NETWORK_WG_IN_USE, NETWORK_WG_IN_USE_MSG

        if '%s%s' % (self.port, self.protocol) in port_used:
            return PORT_PROTOCOL_IN_USE, PORT_PROTOCOL_IN_USE_MSG

        port_used.add('%s%s' % (self.port, self.protocol))

        if self. wg and self.network.split(
                '/')[1] != self.network_wg.split('/')[1]:
            return NETWORK_WG_CIDR_INVALID, NETWORK_WG_CIDR_INVALID_MSG

        if self.wg and '%sudp' % self.port_wg in port_used:
            return PORT_PROTOCOL_IN_USE, PORT_PROTOCOL_IN_USE_MSG

        if self.network_mode == BRIDGE:
            if not self.network_start or not self.network_end:
                return MISSING_PARAMS, MISSING_PARAMS_MSG

            if self.ipv6:
                return BRIDGED_IPV6_INVALID, BRIDGED_IPV6_INVALID_MSG

            if self.links:
                return BRIDGED_SERVER_LINKS_INVALID, \
                    BRIDGED_SERVER_LINKS_INVALID_MSG

            if self.network_links:
                return BRIDGED_NET_LINKS_INVALID, \
                    BRIDGED_NET_LINKS_INVALID_MSG

            if self.replica_count > 1:
                return BRIDGED_REPLICA_INVALID, BRIDGED_REPLICA_INVALID_MSG

            if not utils.check_network_range(
                    self.network, self.network_start, self.network_end):
                return BRIDGE_NETWORK_INVALID, BRIDGE_NETWORK_INVALID_MSG

        if self.links and self.replica_count > 1:
            return SERVER_LINKS_AND_REPLICA, SERVER_LINKS_AND_REPLICA_MSG

        if self.search_domain and not self.dns_servers:
            return SERVER_DOMAIN_NO_DNS, SERVER_DOMAIN_NO_DNS_MSG

        if self.dns_mapping and not self.dns_servers:
            return CLIENT_DNS_MAPPING_NO_DNS, CLIENT_DNS_MAPPING_NO_DNS_MSG

        return None, None
