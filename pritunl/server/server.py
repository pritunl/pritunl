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

import os
import subprocess
import threading
import random
import collections

_resource_lock = collections.defaultdict(threading.Lock)

dict_fields = [
    'id',
    'name',
    'status',
    'start_timestamp',
    'uptime',
    'instances',
    'organizations',
    'groups',
    'ipv6',
    'ipv6_firewall',
    'network',
    'network_mode',
    'network_start',
    'network_end',
    'restrict_routes',
    'bind_address',
    'port',
    'protocol',
    'onc_hostname',
    'dh_param_bits',
    'dh_params',
    'multi_device',
    'dns_servers',
    'search_domain',
    'otp_auth',
    'cipher',
    'hash',
    'jumbo_frames',
    'lzo_compression',
    'inter_client',
    'ping_interval',
    'ping_timeout',
    'link_ping_interval',
    'link_ping_timeout',
    'max_clients',
    'replica_count',
    'dns_mapping',
    'debug',
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
        'bind_address',
        'port',
        'protocol',
        'dh_param_bits',
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
        'link_ping_interval',
        'link_ping_timeout',
        'onc_hostname',
        'dns_mapping',
        'debug',
        'cipher',
        'hash',
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
        'max_clients',
        'replica_count',
        'instances',
        'instances_count',
        'availability_group',
    }
    fields_default = {
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
        'link_ping_interval': 1,
        'link_ping_timeout': 5,
        'debug': False,
        'cipher': 'aes256',
        'hash': 'sha1',
        'jumbo_frames': False,
        'organizations': [],
        'hosts': [],
        'links': [],
        'status': OFFLINE,
        'max_clients': 2000,
        'replica_count': 1,
        'instances': [],
        'instances_count': 0,
    }
    cache_prefix = 'server'

    def __init__(self, name=None, groups=None, network=None, network_mode=None,
            network_start=None, network_end=None, restrict_routes=None,
            ipv6=None, ipv6_firewall=None,bind_address=None, port=None,
            protocol=None, dh_param_bits=None, multi_device=None,
            dns_servers=None, search_domain=None, otp_auth=None,
            cipher=None, hash=None, jumbo_frames=None, lzo_compression=None,
            inter_client=None, ping_interval=None, ping_timeout=None,
            link_ping_interval=None, link_ping_timeout=None, onc_hostname=None,
            max_clients=None, replica_count=None, dns_mapping=None, debug=None,
            **kwargs):
        mongo.MongoObject.__init__(self, **kwargs)

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
        if network_mode is not None:
            self.network_mode = network_mode
        if network_start is not None:
            self.network_start = network_start
        if network_end is not None:
            self.network_end = network_end
        if restrict_routes is not None:
            self.restrict_routes = restrict_routes
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
        if link_ping_interval is not None:
            self.link_ping_interval = link_ping_interval
        if link_ping_timeout is not None:
            self.link_ping_timeout = link_ping_timeout
        if onc_hostname is not None:
            self.onc_hostname = onc_hostname
        if max_clients is not None:
            self.max_clients = max_clients
        if replica_count is not None:
            self.replica_count = replica_count
        if dns_mapping is not None:
            self.dns_mapping = dns_mapping
        if debug is not None:
            self.debug = debug

    @cached_static_property
    def collection(cls):
        return mongo.get_collection('servers')

    @cached_static_property
    def host_collection(cls):
        return mongo.get_collection('hosts')

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
    def org_collection(cls):
        return mongo.get_collection('organizations')

    @cached_static_property
    def host_collection(cls):
        return mongo.get_collection('hosts')

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
            'bind_address': self.bind_address,
            'port': self.port,
            'protocol': self.protocol,
            'dh_param_bits': self.dh_param_bits,
            'groups': self.groups or [],
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
            'jumbo_frames': self.jumbo_frames,
            'lzo_compression': self.lzo_compression,
            'inter_client': True if self.inter_client else False,
            'ping_interval': self.ping_interval,
            'ping_timeout': self.ping_timeout,
            'link_ping_interval': self.link_ping_interval,
            'link_ping_timeout': self.link_ping_timeout,
            'onc_hostname': self.onc_hostname,
            'max_clients': self.max_clients,
            'replica_count': self.replica_count,
            'dns_mapping': True if self.dns_mapping else False,
            'debug': True if self.debug else False,
        }

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

    def ip4to6(self, addr):
        routed_subnet6 = settings.local.host.routed_subnet6
        if routed_subnet6:
            return utils.ip4to6x96(routed_subnet6, self.network, addr)
        return utils.ip4to6x64(settings.vpn.ipv6_prefix, self.network, addr)

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
        users_links = {}

        org_ids = self.org_collection.find({
            '_id': {'$in': self.organizations},
        }, {
            '_id': True,
        }).distinct('_id')

        for doc in self.user_net_link_collection.find({
                    'org_id': {'$in': org_ids},
                }):
            users_links[doc['user_id']] = doc['network']

        user_ids = self.user_collection.find({
            '_id': {'$in': users_links.keys()},
        }, {
            '_id': True,
        }).distinct('_id')

        for user_id in user_ids:
            links.add(users_links[user_id])

        return links

    @property
    def adapter_type(self):
        return 'tap' if self.network_mode == BRIDGE else 'tun'

    @property
    def ca_certificate_list(self):
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
        virtual_vpc_region = None
        virtual_vpc_id = None

        for network_link in self.network_links:
            route_id = network_link.encode('hex')
            routes_dict[network_link] = ({
                'id': route_id,
                'server': self.id,
                'network': network_link,
                'nat': False,
                'nat_interface': None,
                'vpc_region': None,
                'vpc_id': None,
                'virtual_network': False,
                'network_link': True,
                'server_link': False,
                'link_virtual_network': False,
            })

        if include_server_links:
            for link_svr in self.iter_links(fields=('_id', 'network',
                    'network_start', 'network_end', 'routes',
                    'organizations', 'links', 'ipv6')):
                for route in link_svr.get_routes():
                    if route['network'] == '0.0.0.0/0':
                        continue

                    data = routes_dict.get(route['network'], {})

                    data['id'] = route['id']
                    data['server'] = self.id
                    data['network'] = route['network']
                    data['nat'] = route['nat']
                    data['nat_interface'] = route['nat_interface']
                    data['vpc_region'] = None
                    data['vpc_id'] = None
                    data['virtual_network'] = False
                    data['network_link'] = False
                    data['server_link'] = True
                    data['link_virtual_network'] = route['virtual_network']

                    if route['virtual_network']:
                        link_routes.append(data)
                    routes_dict[route['network']] = data

        for route in self.routes:
            route_network = route['network']
            route_id = route_network.encode('hex')

            if route_network == '0.0.0.0/0':
                if not include_default:
                    continue

                routes.append({
                    'id': route_id,
                    'server': self.id,
                    'network': route_network,
                    'nat': route.get('nat', True),
                    'nat_interface': route.get('nat_interface'),
                    'vpc_region': route.get('vpc_region', None),
                    'vpc_id': route.get('vpc_id', None),
                    'virtual_network': False,
                    'network_link': False,
                    'server_link': False,
                    'link_virtual_network': False,
                })

                if include_hidden and self.ipv6:
                    routes.append({
                        'id': route_id,
                        'server': self.id,
                        'network': '::/0',
                        'nat': route.get('nat', True),
                        'nat_interface': route.get('nat_interface'),
                        'vpc_region': route.get('vpc_region'),
                        'vpc_id': route.get('vpc_id'),
                        'virtual_network': False,
                        'network_link': False,
                        'server_link': False,
                        'link_virtual_network': False,
                    })
            elif route_network == 'virtual':
                virtual_vpc_region = route.get('vpc_region', None)
                virtual_vpc_id = route.get('vpc_id', None)
            else:
                if route_network in routes_dict:
                    routes_dict[route_network]['nat'] = route.get('nat', True)
                    routes_dict[route_network]['nat_interface'] = route.get(
                        'nat_interface')
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
                        'nat': route.get('nat', True),
                        'nat_interface': route.get('nat_interface'),
                        'vpc_region': route.get('vpc_region', None),
                        'vpc_id': route.get('vpc_id', None),
                        'virtual_network': False,
                        'network_link': False,
                        'server_link': False,
                        'link_virtual_network': False,
                    }

        routes.append({
            'id': self.network.encode('hex'),
            'server': self.id,
            'network': self.network,
            'nat': False,
            'nat_interface': None,
            'vpc_region': virtual_vpc_region,
            'vpc_id': virtual_vpc_id,
            'virtual_network': True,
            'network_link': False,
            'server_link': False,
            'link_virtual_network': False,
        })

        if self.ipv6:
            routes.append({
                'id': self.network6.encode('hex'),
                'server': self.id,
                'network': self.network6,
                'nat': False,
                'nat_interface': None,
                'vpc_region': virtual_vpc_region,
                'vpc_id': virtual_vpc_id,
                'virtual_network': True,
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

    def upsert_route(self, network, nat_route, nat_interface,
            vpc_region, vpc_id):
        exists = False

        if self.status == ONLINE:
            raise ServerOnlineError(
                'Cannot add route while server is online')

        try:
            network = str(ipaddress.IPNetwork(network))
        except ValueError:
            raise NetworkInvalid('Network address is invalid')

        orig_network = network

        server_link = False
        for route in self.get_routes(include_server_links=True):
            if route['network'] == network:
                server_link = route['server_link']
                if server_link and route['nat'] != nat_route:
                    raise ServerRouteNatServerLink('Cannot nat server link')

                if route['network_link'] and nat_route:
                    raise ServerRouteNatNetworkLink('Cannot nat network link')

        if network == self.network:
            network = 'virtual'

            if nat_route:
                raise ServerRouteNatVirtual('Cannot nat virtual network')
        elif network == '::/0':
            network = '0.0.0.0/0'

        for route in self.routes:
            if route['network'] == network:
                route['nat'] = nat_route
                route['nat_interface'] = nat_interface
                route['vpc_region'] = vpc_region
                route['vpc_id'] = vpc_id
                route['server_link'] = server_link
                exists = True
                break

        if not exists:
            self.routes.append({
                'network': network,
                'nat': nat_route,
                'nat_interface': nat_interface,
                'vpc_region': vpc_region,
                'vpc_id': vpc_id,
                'server_link': server_link,
            })

        return {
            'id': orig_network.encode('hex'),
            'server': self.id,
            'network': orig_network,
            'nat': nat_route,
            'nat_interface': nat_interface,
            'vpc_region': vpc_region,
            'vpc_id': vpc_id,
        }

    def remove_route(self, network):
        if self.status == ONLINE:
            raise ServerOnlineError(
                'Cannot remove route while server is online')

        for i, route in enumerate(self.routes):
            if route['network'] == network:
                self.routes.pop(i)
                break

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
        remotes = []
        spec = {
            '_id': {'$in': self.hosts},
        }
        project = {
            '_id': False,
            'public_address': True,
            'auto_public_address': True,
            'auto_public_host': True,
        }

        for doc in self.host_collection.find(spec, project):
            address = doc.get('auto_public_host') or \
                doc['public_address'] or doc['auto_public_address']
            if settings.conf.port == 443:
                remotes.append('https://%s' % address)
            else:
                remotes.append('https://%s:%s' % (
                    address,
                    settings.conf.port,
                ))

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

    def get_onc_host(self):
        if self.onc_hostname:
            return self.onc_hostname, self.port

        for host, port in self.get_hosts():
            return host, port

        return None, None

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
        queue.stop(spec={
            'type': 'dh_params',
            'server_id': self.id,
        })
        self.remove_primary_user()
        mongo.MongoObject.remove(self)

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
        logger.debug('Creating primary user', 'server',
            server_id=self.id,
        )

        try:
            org = self.iter_orgs().next()
        except StopIteration:
            self.stop()
            raise ServerMissingOrg('Primary user cannot be created ' + \
                'without any organizations', {
                    'server_id': self.id,
                })

        usr = org.new_user(name=SERVER_USER_PREFIX + str(self.id),
            type=CERT_SERVER, resource_id=self.id)
        usr.audit_event('user_created', 'User created for server')

        self.primary_organization = org.id
        self.primary_user = usr.id
        self.commit(('primary_organization', 'primary_user'))

    def remove_primary_user(self):
        logger.debug('Removing primary user', 'server',
            server_id=self.id,
        )

        self.user_collection.remove({
            'resource_id': self.id,
        })

        self.primary_organization = None
        self.primary_user = None

    def add_org(self, org_id):
        if not isinstance(org_id, basestring):
            org_id = org_id.id

        logger.debug('Adding organization to server', 'server',
            server_id=self.id,
            org_id=org_id,
        )

        if org_id in self.organizations:
            logger.debug('Organization already on server, skipping', 'server',
                server_id=self.id,
                org_id=org_id,
            )
            return

        self.organizations.append(org_id)
        self.changed.add('organizations')
        self.generate_ca_cert()
        self._orgs_added.append(org_id)

    def remove_org(self, org_id):
        if not isinstance(org_id, basestring):
            org_id = org_id.id

        if org_id not in self.organizations:
            return

        logger.debug('Removing organization from server', 'server',
            server_id=self.id,
            org_id=org_id,
        )

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
        logger.debug('Adding host to server', 'server',
            server_id=self.id,
            host_id=host_id,
        )

        if host_id in self.hosts:
            logger.debug('Host already on server, skipping', 'server',
                server_id=self.id,
                host_id=host_id,
            )
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

        logger.debug('Removing host from server', 'server',
            server_id=self.id,
            host_id=host_id,
        )

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
        }, {
            '$pull': {
                'hosts': host_id,
            },
        }, {
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
            'start_timestamp': start_timestamp,
            'availability_group': self.get_best_availability_group(),
        }})

        if not response['updatedExisting']:
            raise ServerInstanceSet('Server instances already running. %r', {
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
        logger.debug('Stopping server', 'server',
            server_id=self.id,
        )

        if self.status != ONLINE:
            return

        response = self.collection.update({
            '_id': self.id,
            'status': ONLINE,
        }, {'$set': {
            'status': OFFLINE,
            'start_timestamp': None,
            'instances': [],
            'instances_count': 0,
            'availability_group': None,
        }})

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
        logger.debug('Restarting server', 'server',
            server_id=self.id,
        )
        self.stop()
        self.start()
