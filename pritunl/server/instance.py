from pritunl.server.instance_com import ServerInstanceCom
from pritunl.server.instance_link import ServerInstanceLink
from pritunl.server.bridge import add_interface, rem_interface

from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *
from pritunl import settings
from pritunl import logger
from pritunl import utils
from pritunl import mongo
from pritunl import event
from pritunl import messenger
from pritunl import organization
from pritunl import iptables
from pritunl import ipaddress
from pritunl import plugins
from pritunl import vxlan

import os
import signal
import time
import subprocess
import threading
import traceback
import re
import pymongo
import datetime

_instances = {}
_instances_lock = threading.Lock()

class ServerInstance(object):
    def __init__(self, server):
        self.server = server
        self.id = utils.ObjectId()
        self.interrupt = False
        self.sock_interrupt = False
        self.startup_interrupt = False
        self.clean_exit = False
        self.interface = None
        self.interface_wg = None
        self.wg_started = False
        self.wg_private_key = None
        self.wg_public_key = None
        self.bridge_interface = None
        self.primary_user = None
        self.process = None
        self.vxlan = None
        self.iptables = iptables.Iptables()
        self.iptables_lock = threading.Lock()
        self.iptables_wg = iptables.Iptables()
        self.tun_nat = False
        self.server_links = []
        self.route_advertisements = set()
        self._temp_path = utils.get_temp_path()
        self.ovpn_conf_path = os.path.join(self._temp_path, OVPN_CONF_NAME)
        self.wg_private_key_path = os.path.join(
            self._temp_path, WG_PRIVATE_KEY_NAME)
        self.management_socket_path = os.path.join(
            settings.conf.var_run_path,
            MANAGEMENT_SOCKET_NAME % self.id,
        )

    @cached_static_property
    def collection(cls):
        return mongo.get_collection('servers')

    @cached_static_property
    def user_collection(cls):
        return mongo.get_collection('users')

    @cached_static_property
    def routes_collection(cls):
        return mongo.get_collection('routes_reserve')

    def get_cursor_id(self):
        return messenger.get_cursor_id('servers')

    def is_interrupted(self):
        if _instances.get(self.server.id) != self:
            return True
        return self.sock_interrupt

    def publish(self, message, transaction=None, extra=None):
        extra = extra or {}
        extra.update({
            'server_id': self.server.id,
        })
        messenger.publish('servers', message,
            extra=extra, transaction=transaction)

    def subscribe(self, cursor_id=None, timeout=None):
        for msg in messenger.subscribe('servers', cursor_id=cursor_id,
                timeout=timeout):
            if msg.get('server_id') == self.server.id:
                yield msg

    def resources_acquire(self):
        if self.interface:
            raise TypeError('Server resource already acquired')

        _instances_lock.acquire()
        try:
            instance = _instances.get(self.server.id)
            if instance:
                logger.warning(
                    'Stopping duplicate instance, check date time sync',
                    'server',
                    server_id=self.server.id,
                    instance_id=instance.id,
                )

                try:
                    instance.stop_process()
                except:
                    logger.exception(
                        'Failed to stop duplicate instance', 'server',
                        server_id=self.server.id,
                        instance_id=instance.id,
                    )

                time.sleep(5)

            _instances[self.server.id] = self
        finally:
            _instances_lock.release()

        self.interface = utils.interface_acquire(self.server.adapter_type)
        if self.server.wg:
            self.interface_wg = utils.interface_acquire('wg')

    def resources_release(self):
        interface = self.interface
        if interface:
            utils.interface_release(self.server.adapter_type, interface)
            self.interface = None
        interface_wg = self.interface_wg
        if interface_wg:
            utils.interface_release('wg', interface_wg)
            self.interface_wg = None

        _instances_lock.acquire()
        try:
            if _instances.get(self.server.id) == self:
                _instances.pop(self.server.id)
        finally:
            _instances_lock.release()

    def generate_ovpn_conf(self):
        if not self.server.primary_organization or \
                not self.server.primary_user:
            self.server.create_primary_user()

        if self.server.primary_organization not in self.server.organizations:
            self.server.remove_primary_user()
            self.server.create_primary_user()

        primary_org = organization.get_by_id(
            self.server.primary_organization)
        if not primary_org:
            self.server.create_primary_user()
            primary_org = organization.get_by_id(
                id=self.server.primary_organization)

        self.primary_user = primary_org.get_user(self.server.primary_user)
        if not self.primary_user:
            self.server.create_primary_user()
            primary_org = organization.get_by_id(
                id=self.server.primary_organization)
            self.primary_user = primary_org.get_user(
                self.server.primary_user)

        gateway = utils.get_network_gateway(self.server.network)
        gateway6 = utils.get_network_gateway(self.server.network6)

        push = ''
        routes = []
        for route in self.server.get_routes(include_default=False):
            routes.append(route['network'])
            if route['virtual_network'] and not route.get('wg_network'):
                continue

            metric = route.get('metric')
            if metric:
                metric_def = ' vpn_gateway %s' % metric
                metric = ' %s' % metric
            else:
                metric_def = ''
                metric = ''

            network = route['network']
            netmap = route.get('nat_netmap')
            if netmap:
                network = netmap

            if route['net_gateway']:
                if ':' in network:
                    push += 'push "route-ipv6 %s net_gateway%s"\n' % (
                        network, metric)
                else:
                    push += 'push "route %s %s net_gateway%s"\n' % (
                        utils.parse_network(network) + (metric,))
            elif not route.get('network_link'):
                if ':' in network:
                    push += 'push "route-ipv6 %s%s"\n' % (
                        network, metric_def)
                else:
                    push += 'push "route %s %s%s"\n' % (
                        utils.parse_network(network) + (metric_def,))
            else:
                if ':' in network:
                    push += 'route-ipv6 %s %s%s\n' % (
                        network, gateway6, metric)
                else:
                    push += 'route %s %s %s%s\n' % (
                        utils.parse_network(network) + (gateway, metric))

        for link_svr in self.server.iter_links(fields=(
                '_id', 'wg', 'network', 'network_wg', 'local_networks',
                'network_start', 'network_end', 'organizations', 'routes',
                'links', 'ipv6', 'replica_count', 'network_mode')):
            if self.server.id < link_svr.id:
                for route in link_svr.get_routes(include_default=False):
                    network = route['network']
                    metric = route.get('metric')
                    if metric:
                        metric = ' %s' % metric
                    else:
                        metric = ''

                    if route['net_gateway']:
                        continue

                    netmap = route.get('nat_netmap')
                    if netmap:
                        network = netmap

                    if ':' in network:
                        push += 'route-ipv6 %s %s%s\n' % (
                            network, gateway6, metric)
                    else:
                        push += 'route %s %s %s%s\n' % (
                            utils.parse_network(network) +
                            (gateway, metric)
                        )

        if self.vxlan:
            push += 'push "route %s %s"\n' % utils.parse_network(
                self.vxlan.vxlan_net)
            if self.server.ipv6:
                push += 'push "route-ipv6 %s"\n' % self.vxlan.vxlan_net6

        if self.server.network_mode == BRIDGE:
            host_int_data = self.host_interface_data
            host_address = host_int_data['address']
            host_netmask = host_int_data['netmask']

            server_line = 'server-bridge %s %s %s %s' % (
                host_address,
                host_netmask,
                self.server.network_start,
                self.server.network_end,
            )
        else:
            server_line = 'server %s %s' % utils.parse_network(
                self.server.network)

            if self.server.ipv6:
                server_line += '\nserver-ipv6 ' + self.server.network6

        if self.server.protocol == 'tcp':
            if (self.server.ipv6 or settings.vpn.ipv6) and \
                    not self.server.bind_address:
                protocol = 'tcp6-server'
            else:
                protocol = 'tcp-server'
        elif self.server.protocol == 'udp':
            if (self.server.ipv6 or settings.vpn.ipv6) and \
                    not self.server.bind_address:
                protocol = 'udp6'
            else:
                protocol = 'udp'
        else:
            raise ValueError('Unknown protocol')

        if utils.check_openvpn_ver():
            server_ciphers = SERVER_CIPHERS
            server_conf_template = OVPN_INLINE_SERVER_CONF
        else:
            server_ciphers = SERVER_CIPHERS_OLD
            server_conf_template = OVPN_INLINE_SERVER_CONF_OLD

        server_conf = server_conf_template % (
            self.server.port,
            protocol,
            self.interface,
            server_line,
            self.management_socket_path,
            self.server.max_clients,
            self.server.ping_interval,
            self.server.ping_timeout + 20,
            self.server.ping_interval,
            self.server.ping_timeout,
            server_ciphers[self.server.cipher],
            HASHES[self.server.hash],
            4 if self.server.debug else 1,
            8 if self.server.debug else 3,
        )

        if self.server.bind_address:
            server_conf += 'local %s\n' % self.server.bind_address

        if self.server.inter_client:
            server_conf += 'client-to-client\n'

        if self.server.multi_device:
            server_conf += 'duplicate-cn\n'

        if self.server.protocol == 'udp':
            server_conf += 'replay-window 128\n'

        if self.server.mss_fix:
            server_conf += 'mssfix %s\n' % self.server.mss_fix

        # Pritunl v0.10.x did not include comp-lzo in client conf
        # if lzo_compression is adaptive dont include comp-lzo in server conf
        if self.server.lzo_compression == ADAPTIVE:
            pass
        elif self.server.lzo_compression:
            server_conf += 'comp-lzo yes\npush "comp-lzo yes"\n'
        else:
            server_conf += 'comp-lzo no\npush "comp-lzo no"\n'

        server_conf += JUMBO_FRAMES[self.server.jumbo_frames]

        if push:
            server_conf += push

        if self.server.debug:
            self.server.output.push_message('Server conf:')
            for conf_line in server_conf.split('\n'):
                if conf_line:
                    self.server.output.push_message('  ' + conf_line)

        if settings.local.sub_plan and \
                'enterprise' in settings.local.sub_plan:
            returns = plugins.caller(
                'server_config',
                host_id=settings.local.host_id,
                host_name=settings.local.host.name,
                server_id=self.server.id,
                server_name=self.server.name,
                port=self.server.port,
                protocol=self.server.protocol,
                ipv6=self.server.ipv6,
                ipv6_firewall=self.server.ipv6_firewall,
                network=self.server.network,
                network6=self.server.network6,
                network_mode=self.server.network_mode,
                network_start=self.server.network_start,
                network_stop=self.server.network_end,
                restrict_routes=self.server.restrict_routes,
                bind_address=self.server.bind_address,
                onc_hostname=None,
                dh_param_bits=self.server.dh_param_bits,
                multi_device=self.server.multi_device,
                dns_servers=self.server.dns_servers,
                search_domain=self.server.search_domain,
                otp_auth=self.server.otp_auth,
                cipher=self.server.cipher,
                hash=self.server.hash,
                inter_client=self.server.inter_client,
                ping_interval=self.server.ping_interval,
                ping_timeout=self.server.ping_timeout,
                link_ping_interval=self.server.link_ping_interval,
                link_ping_timeout=self.server.link_ping_timeout,
                allowed_devices=self.server.allowed_devices,
                max_clients=self.server.max_clients,
                replica_count=self.server.replica_count,
                dns_mapping=self.server.dns_mapping,
                debug=self.server.debug,
                routes=routes,
                interface=self.interface,
                bridge_interface=self.bridge_interface,
                vxlan=self.vxlan,
            )

            if returns:
                for return_val in returns:
                    if not return_val:
                        continue
                    server_conf += return_val.strip() + '\n'

        server_conf += '<ca>\n%s\n</ca>\n' % self.server.ca_certificate

        if self.server.tls_auth:
            server_conf += \
                'key-direction 0\n<tls-auth>\n%s\n</tls-auth>\n' % (
                self.server.tls_auth_key)

        server_conf += '<cert>\n%s\n</cert>\n' % utils.get_cert_block(
            self.primary_user.certificate)
        server_conf += '<key>\n%s\n</key>\n' % self.primary_user.private_key
        server_conf += '<dh>\n%s\n</dh>\n' % self.server.dh_params

        with open(self.ovpn_conf_path, 'w') as ovpn_conf:
            os.chmod(self.ovpn_conf_path, 0o600)
            ovpn_conf.write(server_conf)

    def enable_ip_forwarding(self):
        try:
            utils.check_output_logged(
                ['sysctl', '-w', 'net.ipv4.ip_forward=1'])
        except subprocess.CalledProcessError:
            logger.exception('Failed to enable IP forwarding', 'server',
                server_id=self.server.id,
            )
            raise

        if self.server.ipv6:
            keys = []
            output = utils.check_output_logged(['sysctl', 'net.ipv6.conf'])

            for line in output.split('\n'):
                if '.accept_ra =' in line:
                    keys.append(line.split('=')[0].strip())

            try:
                for key in keys:
                    utils.check_output_logged([
                        'sysctl',
                        '-w',
                        '%s=2' % key,
                    ])
                utils.check_output_logged(
                    ['sysctl', '-w', 'net.ipv6.conf.all.forwarding=1'])
            except subprocess.CalledProcessError:
                logger.exception(
                    'Failed to enable IPv6 forwarding', 'server',
                    server_id=self.server.id,
                )

    def bridge_start(self):
        if self.server.network_mode != BRIDGE:
            return

        try:
            self.bridge_interface, self.host_interface_data = add_interface(
                self.server.network,
                self.interface,
            )
        except BridgeLookupError:
            self.server.output.push_output(
                'ERROR Failed to find bridged network interface')
            raise

    def bridge_stop(self):
        if self.server.network_mode != BRIDGE:
            return

        rem_interface(self.server.network, self.interface)

    def generate_iptables_rules(self):
        server_addr = utils.get_network_gateway(self.server.network)
        server_addr6 = utils.get_network_gateway(self.server.network6)
        ipv6_firewall = self.server.ipv6_firewall and \
            settings.local.host.routed_subnet6

        self.iptables.id = self.server.id
        self.iptables.ipv6 = self.server.ipv6
        self.iptables.server_addr = server_addr
        self.iptables.server_addr6 = server_addr6
        self.iptables.virt_interface = self.interface
        self.iptables.virt_network = self.server.network
        self.iptables.virt_network6 = self.server.network6
        self.iptables.ipv6_firewall = ipv6_firewall
        self.iptables.inter_client = self.server.inter_client
        self.iptables.restrict_routes = self.server.restrict_routes

        if self.server.wg:
            self.iptables_wg.add_route(self.server.network_wg)
            self.iptables_wg.add_route(self.server.network6_wg)

        try:
            routes_output = utils.check_output_logged(['route', '-n'])
        except subprocess.CalledProcessError:
            logger.exception('Failed to get IP routes', 'server',
                server_id=self.server.id,
            )
            raise

        routes = []
        default_interface = None
        for line in routes_output.splitlines():
            line_split = line.split()
            if len(line_split) < 8 or not re.match(IP_REGEX, line_split[0]):
                continue
            if line_split[0] not in routes:
                if line_split[0] == '0.0.0.0':
                    if default_interface:
                        continue
                    default_interface = line_split[7]

                routes.append((
                    ipaddress.ip_network('%s/%s' % (line_split[0],
                        utils.subnet_to_cidr(line_split[2])), strict=False),
                    line_split[7]
                ))
        routes.reverse()

        if not default_interface:
            raise IptablesError('Failed to find default network interface')

        routes6 = []
        default_interface6 = None
        default_interface6_alt = None
        if self.server.ipv6:
            try:
                routes_output = utils.check_output_logged(
                    ['route', '-n', '-A', 'inet6'])
            except subprocess.CalledProcessError:
                logger.exception('Failed to get IPv6 routes', 'server',
                    server_id=self.server.id,
                )
                raise

            for line in routes_output.splitlines():
                line_split = line.split()

                if len(line_split) < 7:
                    continue

                try:
                    route_network = ipaddress.IPv6Network(line_split[0])
                except (ipaddress.AddressValueError, ValueError):
                    continue

                if line_split[0] == '::/0':
                    if default_interface6 or line_split[6] == 'lo':
                        continue
                    default_interface6 = line_split[6]

                if line_split[0] == 'ff00::/8':
                    if default_interface6_alt or line_split[6] == 'lo':
                        continue
                    default_interface6_alt = line_split[6]

                routes6.append((
                    route_network,
                    line_split[6],
                ))

            default_interface6 = default_interface6 or default_interface6_alt
            if not default_interface6:
                raise IptablesError(
                    'Failed to find default IPv6 network interface')
        routes6.reverse()

        interfaces = set()
        interfaces6 = set()

        for route in self.server.get_routes(
                    include_hidden=True,
                    include_server_links=True,
                    include_default=True,
                ):
            if route['virtual_network'] or route['link_virtual_network']:
                self.iptables.add_nat_network(route['network'])

            if route['virtual_network'] or route['net_gateway']:
                continue

            network = route['network']
            is6 = ':' in network
            network_obj = ipaddress.ip_network(network, strict=False)

            interface = route['nat_interface']
            if is6:
                if not interface:
                    for route_net, route_intf in routes6:
                        if network_obj in route_net:
                            interface = route_intf
                            break

                    if not interface:
                        logger.info(
                            'Failed to find interface for local ' + \
                                'IPv6 network route, using default route',
                                'server',
                            server_id=self.server.id,
                            network=network,
                        )
                        interface = default_interface6
                interfaces6.add(interface)
            else:
                if not interface:
                    for route_net, route_intf in routes:
                        if network_obj in route_net:
                            interface = route_intf
                            break

                    if not interface:
                        logger.info(
                            'Failed to find interface for local ' + \
                                'network route, using default route',
                                'server',
                            server_id=self.server.id,
                            network=network,
                        )
                        interface = default_interface
                interfaces.add(interface)

            nat = route['nat']
            if network == '::/0' and self.server.ipv6 and \
                    settings.local.host.routed_subnet6:
                nat = False

            if nat and route['nat_netmap']:
                self.iptables.add_netmap(network, route['nat_netmap'])
                self.iptables.add_route(
                    route['nat_netmap'],
                    nat=False,
                )

            self.iptables.add_route(
                network,
                nat=nat,
                nat_interface=interface,
            )

        if self.vxlan:
            self.iptables.add_route(self.vxlan.vxlan_net)
            if self.server.ipv6:
                self.iptables.add_route(self.vxlan.vxlan_net6)

        self.iptables.generate()

    def generate_iptables_rules_wg(self):
        server_addr = utils.get_network_gateway(self.server.network_wg)
        server_addr6 = utils.get_network_gateway(self.server.network6_wg)
        ipv6_firewall = self.server.ipv6_firewall and \
            settings.local.host.routed_subnet6

        self.iptables_wg.id = self.server.id
        self.iptables_wg.ipv6 = self.server.ipv6
        self.iptables_wg.server_addr = server_addr
        self.iptables_wg.server_addr6 = server_addr6
        self.iptables_wg.virt_interface = self.interface_wg
        self.iptables_wg.virt_network = self.server.network_wg
        self.iptables_wg.virt_network6 = self.server.network6_wg
        self.iptables_wg.ipv6_firewall = ipv6_firewall
        self.iptables_wg.inter_client = self.server.inter_client
        self.iptables_wg.restrict_routes = self.server.restrict_routes

        self.iptables_wg.add_route(self.server.network)
        self.iptables_wg.add_route(self.server.network6)

        try:
            routes_output = utils.check_output_logged(['route', '-n'])
        except subprocess.CalledProcessError:
            logger.exception('Failed to get IP routes', 'server',
                server_id=self.server.id,
            )
            raise

        routes = []
        default_interface = None
        for line in routes_output.splitlines():
            line_split = line.split()
            if len(line_split) < 8 or not re.match(IP_REGEX, line_split[0]):
                continue
            if line_split[0] not in routes:
                if line_split[0] == '0.0.0.0':
                    if default_interface:
                        continue
                    default_interface = line_split[7]

                routes.append((
                    ipaddress.ip_network('%s/%s' % (line_split[0],
                        utils.subnet_to_cidr(line_split[2])), strict=False),
                    line_split[7]
                ))
        routes.reverse()

        if not default_interface:
            raise IptablesError('Failed to find default network interface')

        routes6 = []
        default_interface6 = None
        default_interface6_alt = None
        if self.server.ipv6:
            try:
                routes_output = utils.check_output_logged(
                    ['route', '-n', '-A', 'inet6'])
            except subprocess.CalledProcessError:
                logger.exception('Failed to get IPv6 routes', 'server',
                    server_id=self.server.id,
                )
                raise

            for line in routes_output.splitlines():
                line_split = line.split()

                if len(line_split) < 7:
                    continue

                try:
                    route_network = ipaddress.IPv6Network(line_split[0])
                except (ipaddress.AddressValueError, ValueError):
                    continue

                if line_split[0] == '::/0':
                    if default_interface6 or line_split[6] == 'lo':
                        continue
                    default_interface6 = line_split[6]

                if line_split[0] == 'ff00::/8':
                    if default_interface6_alt or line_split[6] == 'lo':
                        continue
                    default_interface6_alt = line_split[6]

                routes6.append((
                    route_network,
                    line_split[6],
                ))

            default_interface6 = default_interface6 or default_interface6_alt
            if not default_interface6:
                raise IptablesError(
                    'Failed to find default IPv6 network interface')
        routes6.reverse()

        interfaces = set()
        interfaces6 = set()

        for route in self.server.get_routes(
            include_hidden=True,
            include_server_links=True,
            include_default=True,
        ):
            if route['virtual_network'] or route['net_gateway']:
                continue

            network = route['network']
            is6 = ':' in network
            network_obj = ipaddress.ip_network(network, strict=False)

            interface = route['nat_interface']
            if is6:
                if not interface:
                    for route_net, route_intf in routes6:
                        if network_obj in route_net:
                            interface = route_intf
                            break

                    if not interface:
                        logger.info(
                            'Failed to find interface for local ' + \
                            'IPv6 network route, using default route',
                            'server',
                            server_id=self.server.id,
                            network=network,
                            )
                        interface = default_interface6
                interfaces6.add(interface)
            else:
                if not interface:
                    for route_net, route_intf in routes:
                        if network_obj in route_net:
                            interface = route_intf
                            break

                    if not interface:
                        logger.info(
                            'Failed to find interface for local ' + \
                            'network route, using default route',
                            'server',
                            server_id=self.server.id,
                            network=network,
                            )
                        interface = default_interface
                interfaces.add(interface)

            nat = route['nat']
            if network == '::/0' and self.server.ipv6 and \
                settings.local.host.routed_subnet6:
                nat = False

            if nat and route['nat_netmap']:
                self.iptables_wg.add_netmap(network, route['nat_netmap'])
                self.iptables_wg.add_route(
                    route['nat_netmap'],
                    nat=False,
                )

            self.iptables_wg.add_route(
                network,
                nat=nat,
                nat_interface=interface,
            )

        if self.vxlan:
            self.iptables_wg.add_route(self.vxlan.vxlan_net)
            if self.server.ipv6:
                self.iptables_wg.add_route(self.vxlan.vxlan_net6)

        self.iptables_wg.generate()

    def enable_iptables_tun_nat(self):
        self.iptables_lock.acquire()
        try:
            if self.tun_nat:
                return
            self.tun_nat = True

            rule = [
                'POSTROUTING',
                '-t', 'nat',
                '-o', self.interface,
                '-j', 'MASQUERADE',
            ]
            self.iptables.add_rule(rule)
            self.iptables.add_rule6(rule)

            if self.server.wg:
                rule = [
                    'POSTROUTING',
                    '-t', 'nat',
                    '-o', self.interface_wg,
                    '-j', 'MASQUERADE',
                ]
                self.iptables_wg.add_rule(rule)
                self.iptables_wg.add_rule6(rule)
        finally:
            self.iptables_lock.release()

    def stop_process(self):
        self.sock_interrupt = True

        for instance_link in self.server_links:
            instance_link.stop()

        if self.process:
            terminated = utils.stop_process(self.process)
        else:
            terminated = True

        if not terminated:
            logger.error('Failed to stop server process', 'server',
                server_id=self.server.id,
                instance_id=self.id,
            )
            return False

        return terminated

    def openvpn_start(self):
        try:
            return subprocess.Popen(['openvpn', self.ovpn_conf_path],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except OSError:
            logger.exception('Failed to start ovpn process', 'server',
                server_id=self.server.id,
            )
            self.server.output.push_output(traceback.format_exc())
            raise

    def interrupter_sleep(self, length):
        if check_global_interrupt() or self.interrupt:
            return True
        while True:
            sleep = min(0.5, length)
            time.sleep(sleep)
            length -= sleep
            if check_global_interrupt() or self.interrupt:
                return True
            elif length <= 0:
                return False

    @interrupter
    def _openvpn_stdout(self):
        while True:
            line = self.process.stdout.readline()
            if not line:
                if self.process.poll() is not None or self.is_interrupted():
                    return
                time.sleep(0.05)
                continue

            yield

            try:
                self.server.output.push_output(line.decode())
            except:
                logger.exception('Failed to push vpn output', 'server',
                    server_id=self.server.id,
                )

            yield

    @interrupter
    def _openvpn_stderr(self):
        while True:
            line = self.process.stderr.readline()
            if not line:
                if self.process.poll() is not None or self.is_interrupted():
                    return
                time.sleep(0.05)
                continue

            yield

            try:
                self.server.output.push_output(line.decode())
            except:
                logger.exception('Failed to push vpn output', 'server',
                    server_id=self.server.id,
                )

            yield

    def openvpn_output(self):
        thread = threading.Thread(target=self._openvpn_stdout)
        thread.daemon = True
        thread.start()

        thread = threading.Thread(target=self._openvpn_stderr)
        thread.daemon = True
        thread.start()

    @interrupter
    def _sub_thread(self, cursor_id):
        try:
            for msg in self.subscribe(cursor_id=cursor_id):
                yield

                if self.interrupt:
                    return
                message = msg['message']

                try:
                    if message == 'stop':
                        if self.stop_process():
                            self.clean_exit = True
                    elif message == 'rebalance':
                        if settings.local.host.availability_group != \
                                msg['availability_group']:
                            if self.stop_process():
                                self.clean_exit = True
                    elif message == 'force_stop':
                        for instance_link in self.server_links:
                            instance_link.stop()

                        self.clean_exit = True
                        for _ in range(10):
                            self.process.send_signal(signal.SIGKILL)
                            time.sleep(0.01)
                except OSError:
                    pass
        except GeneratorExit:
            self.stop_process()
        except:
            logger.exception('Exception in messaging thread', 'server',
                server_id=self.server.id,
            )
            self.stop_process()

    @interrupter
    def _startup_keepalive_thread(self):
        try:
            error_count = 0

            while not self.startup_interrupt:
                try:
                    doc = self.collection.find_and_modify({
                        '_id': self.server.id,
                        'availability_group': \
                            settings.local.host.availability_group,
                        'instances.instance_id': self.id,
                    }, {'$set': {
                        'instances.$.ping_timestamp': utils.now(),
                    }}, fields={
                        '_id': False,
                        'instances': True,
                    }, new=True)

                    yield

                    if not doc:
                        doc = self.collection.find_one({
                            '_id': self.server.id,
                        })

                        doc_hosts = ((doc or {}).get('hosts') or [])
                        if settings.local.host_id in doc_hosts:
                            logger.error(
                                'Startup doc lost, stopping server', 'server',
                                server_id=self.server.id,
                                instance_id=self.id,
                                cur_timestamp=utils.now(),
                            )

                        self.sock_interrupt = True
                        return
                    else:
                        error_count = 0

                    yield
                except GeneratorExit:
                    self.stop_process()
                except:
                    error_count += 1
                    if error_count >= 10 and self.stop_process():
                        logger.exception(
                            'Failed to update startup ping, stopping server',
                            'server',
                            server_id=self.server.id,
                        )
                        break

                    logger.exception('Failed to update startup ping',
                        'server',
                        server_id=self.server.id,
                    )
                    time.sleep(1)

                yield interrupter_sleep(3)
        except GeneratorExit:
            self.stop_process()

    @interrupter
    def _keep_alive_thread(self):
        try:
            error_count = 0

            while not self.interrupt:
                if settings.local.vpn_state == DISABLED:
                    logger.warning(
                        'VPN server disabled',
                        'server',
                        message=settings.local.notification,
                    )
                    if self.stop_process():
                        return
                    continue

                try:
                    doc = self.collection.find_and_modify({
                        '_id': self.server.id,
                        'availability_group': \
                            settings.local.host.availability_group,
                        'instances.instance_id': self.id,
                    }, {'$set': {
                        'instances.$.ping_timestamp': utils.now(),
                    }}, fields={
                        '_id': False,
                        'instances': True,
                    }, new=True)

                    yield

                    if not doc:
                        doc = self.collection.find_one({
                            '_id': self.server.id,
                        })

                        doc_hosts = ((doc or {}).get('hosts') or [])
                        if settings.local.host_id in doc_hosts:
                            logger.error(
                                'Instance doc lost, stopping server. ' +
                                'Check datetime settings',
                                'server',
                                server_id=self.server.id,
                                instance_id=self.id,
                                cur_timestamp=utils.now(),
                            )

                        if self.stop_process():
                            break
                        else:
                            time.sleep(1)
                            continue
                    else:
                        error_count = 0

                    yield
                except GeneratorExit:
                    self.stop_process()
                except:
                    error_count += 1
                    if error_count >= 10 and self.stop_process():
                        logger.exception(
                            'Failed to update server ping, stopping server',
                            'server',
                            server_id=self.server.id,
                        )
                        break

                    logger.exception('Failed to update server ping',
                        'server',
                        server_id=self.server.id,
                    )
                    time.sleep(2)

                yield interrupter_sleep(settings.vpn.server_ping)
        except GeneratorExit:
            self.stop_process()

    @interrupter
    def _route_ad_keep_alive_thread(self):
        try:
            while not self.interrupt:
                try:
                    for ra_id in self.route_advertisements.copy():
                        yield

                        response = self.routes_collection.update_one({
                            '_id': ra_id,
                            'instance_id': self.id,
                        }, {'$set': {
                            'timestamp': utils.now(),
                        }})

                        if not response.modified_count:
                            logger.error(
                                'Lost route advertisement reserve',
                                'server',
                                server_id=self.server.id,
                                instance_id=self.id,
                                route_id=ra_id,
                            )
                            try:
                                self.route_advertisements.remove(ra_id)
                            except KeyError:
                                pass

                    yield
                except GeneratorExit:
                    pass
                except:
                    logger.exception(
                        'Failed to update route advertisement',
                        'server',
                        server_id=self.server.id,
                    )
                    time.sleep(1)

                yield interrupter_sleep(settings.vpn.route_ping)
        except GeneratorExit:
            pass

    def _iptables_thread(self):
        if not settings.vpn.iptables_update:
            return

        if self.interrupter_sleep(settings.vpn.iptables_update_rate):
            return

        while not self.interrupt:
            try:
                self.iptables.upsert_rules(log=True)
                if self.server.wg:
                    self.iptables_wg.upsert_rules(log=True)
                if self.interrupter_sleep(
                        settings.vpn.iptables_update_rate):
                    return
            except:
                logger.exception('Error in iptables thread', 'server',
                    server_id=self.server.id,
                )
                time.sleep(1)

    def init_route_advertisements(self):
        for route in self.server.get_routes(include_server_links=True):
            advertise = route['advertise']
            vpc_region = route['vpc_region']
            vpc_id = route['vpc_id']
            network = route['network']

            if route['net_gateway']:
                continue

            netmap = route.get('nat_netmap')
            if netmap:
                network = netmap

            if advertise or (vpc_region and vpc_id):
                self.reserve_route_advertisement(
                    vpc_region, vpc_id, network)

    def clear_route_advertisements(self):
        for ra_id in self.route_advertisements.copy():
            self.routes_collection.remove({
                '_id': ra_id,
            })

    def reserve_route_advertisement(self, vpc_region, vpc_id, network):
        cloud_provider = settings.app.cloud_provider
        if not cloud_provider:
            return

        ra_id = '%s_%s_%s' % (self.server.id, vpc_id, network)
        timestamp_spec = utils.now() - datetime.timedelta(
            seconds=settings.vpn.route_ping_ttl)

        try:
            self.routes_collection.update_one({
                '_id': ra_id,
                'timestamp': {'$lt': timestamp_spec},
            }, {'$set': {
                'instance_id': self.id,
                'server_id': self.server.id,
                'vpc_region': vpc_region,
                'vpc_id': vpc_id,
                'network': network,
                'timestamp': utils.now(),
            }}, upsert=True)

            if cloud_provider == 'aws':
                utils.add_vpc_route(network)
            elif cloud_provider == 'oracle':
                utils.oracle_add_route(network)
            else:
                logger.error('Unknown cloud provider type', 'server',
                    cloud_provider=settings.app.cloud_provider,
                    network=network,
                )

            if self.vxlan:
                if network == self.server.network:
                    vxlan_net = self.vxlan.vxlan_net
                    if cloud_provider == 'aws':
                        utils.add_vpc_route(vxlan_net)
                    elif cloud_provider == 'oracle':
                        utils.oracle_add_route(vxlan_net)

                elif network == self.server.network6:
                    vxlan_net6 = utils.net4to6x64(
                        settings.vpn.ipv6_prefix,
                        self.vxlan.vxlan_net,
                    )
                    if cloud_provider == 'aws':
                        utils.add_vpc_route(vxlan_net6)
                    elif cloud_provider == 'oracle':
                        utils.oracle_add_route(vxlan_net6)

            self.route_advertisements.add(ra_id)
        except pymongo.errors.DuplicateKeyError:
            return
        except:
            logger.exception('Failed to add vpc route', 'server',
                server_id=self.server.id,
                instance_id=self.id,
                vpc_region=vpc_region,
                vpc_id=vpc_id,
                network=network,
            )

    def start_wg(self):
        self.wg_started = True

        try:
            utils.check_call_silent([
                'ip', 'link',
                'add', 'dev', 'wgh0',
                'type', 'wireguard',
            ])
        except subprocess.CalledProcessError:
            pass

        try:
            private_key = utils.check_output_logged([
                'wg', 'genkey',
            ])
        except subprocess.CalledProcessError:
            logger.exception('Failed to generate wg private key', 'server',
                server_id=self.server.id,
            )
            raise

        try:
            public_key = utils.check_output_logged([
                'wg', 'pubkey',
            ], input=private_key)
        except subprocess.CalledProcessError:
            logger.exception('Failed to get wg public key', 'server',
                server_id=self.server.id,
            )
            raise

        with open(self.wg_private_key_path, 'w') as privatekey_file:
            os.chmod(self.ovpn_conf_path, 0o600)
            privatekey_file.write(private_key)

        self.wg_private_key = private_key.strip()
        self.wg_public_key = public_key.strip()

        try:
            utils.check_call_silent([
                'ip', 'link',
                'del', 'dev', self.interface_wg,
            ])
        except subprocess.CalledProcessError:
            pass

        try:
            utils.check_output_logged([
                'ip', 'link',
                'add', 'dev', self.interface_wg,
                'type', 'wireguard',
            ])
        except subprocess.CalledProcessError:
            logger.exception('Failed to add wg interface', 'server',
                server_id=self.server.id,
            )
            raise

        server_addr = utils.get_network_gateway_cidr(
            self.server.network_wg)
        try:
            utils.check_output_logged([
                'ip', 'address',
                'add', 'dev', self.interface_wg,
                server_addr,
            ])
        except subprocess.CalledProcessError:
            logger.exception('Failed to add wg ip', 'server',
                server_id=self.server.id,
            )
            raise

        if self.server.ipv6:
            server_addr6 = utils.get_network_gateway_cidr(
                self.server.network6_wg)

            try:
                utils.check_output_logged([
                    'ip', '-6', 'address',
                    'add', 'dev', self.interface_wg,
                    server_addr6,
                ])
            except subprocess.CalledProcessError:
                logger.exception('Failed to add wg ipv6', 'server',
                    server_id=self.server.id,
                )
                raise

        try:
            utils.check_output_logged([
                'wg', 'set', self.interface_wg,
                'listen-port', '%s' % self.server.port_wg,
                'private-key', self.wg_private_key_path,
            ])
        except subprocess.CalledProcessError:
            logger.exception('Failed to configure wg', 'server',
                server_id=self.server.id,
            )
            raise

        try:
            utils.check_output_logged([
                'ip', 'link',
                'set', self.interface_wg, 'up',
            ])
        except subprocess.CalledProcessError:
            logger.exception('Failed to start wg interface', 'server',
                server_id=self.server.id,
            )
            raise

    def stop_wg(self):
        if not self.wg_started:
            return

        try:
            utils.check_output_logged([
                'ip', 'link',
                'set', self.interface_wg, 'down',
            ])
        except subprocess.CalledProcessError:
            logger.exception('Failed to stop wg interface', 'server',
                server_id=self.server.id,
            )

        try:
            utils.check_output_logged([
                'ip', 'link',
                'del', 'dev', self.interface_wg,
            ])
        except subprocess.CalledProcessError:
            logger.exception('Failed to del wg interface', 'server',
                server_id=self.server.id,
            )

    def connect_wg(self, wg_public_key, virt_address, virt_address6,
            network_links, network_links6):
        allowed_ips = virt_address.split('/')[0] + '/32'
        if self.server.ipv6 and virt_address6:
            allowed_ips += ',' + virt_address6.split('/')[0] + '/128'

        for network_link in network_links:
            allowed_ips += ',' + network_link

        for network_link in network_links6:
            allowed_ips += ',' + network_link

        try:
            utils.check_output_logged([
                'wg', 'set', self.interface_wg,
                'peer', wg_public_key,
                'persistent-keepalive', '10',
                'allowed-ips', allowed_ips,
            ])
        except subprocess.CalledProcessError:
            logger.exception('Failed to add wg peer', 'server',
                server_id=self.server.id,
            )
            raise

    def disconnect_wg(self, wg_public_key):
        for i in range(10):
            try:
                utils.check_output_logged([
                    'wg', 'set', self.interface_wg,
                    'peer', wg_public_key,
                    'remove',
                ])
                break
            except subprocess.CalledProcessError:
                if i < 9:
                    logger.exception(
                        'Failed to remove wg peer, retrying...',
                        'server',
                        server_id=self.server.id,
                    )
                else:
                    logger.exception(
                        'Failed to remove wg peer, stopping server',
                        'server',
                        server_id=self.server.id,
                    )
                    self.stop_process()
            time.sleep(0.5)

        self.instance_com.clients.disconnected(wg_public_key)

    def start_threads(self, cursor_id):
        thread = threading.Thread(target=self._sub_thread, args=(cursor_id,))
        thread.daemon = True
        thread.start()

        thread = threading.Thread(target=self._keep_alive_thread)
        thread.daemon = True
        thread.start()

        thread = threading.Thread(target=self._route_ad_keep_alive_thread)
        thread.daemon = True
        thread.start()

        thread = threading.Thread(target=self._iptables_thread)
        thread.daemon = True
        thread.start()

    def _run_thread(self, send_events):
        from pritunl.server.utils import get_by_id

        logger.info('Starting vpn server', 'server',
            server_id=self.server.id,
            instance_id=self.id,
            instances=self.server.instances,
            instances_count=self.server.instances_count,
            route_count=len(self.server.routes),
            network=self.server.network,
            network6=self.server.network6,
            host_id=settings.local.host.id,
            host_address=settings.local.host.local_addr,
            host_address6=settings.local.host.local_addr6,
            host_networks=settings.local.host.local_networks,
            cur_timestamp=utils.now(),
            libipt=settings.vpn.lib_iptables,
        )

        def timeout():
            logger.error('Server startup timed out, stopping server',
                'server',
                server_id=self.server.id,
                instance_id=self.id,
                state=self.state,
            )
            self.stop_process()

        startup_keepalive_thread = threading.Thread(
            target=self._startup_keepalive_thread)
        startup_keepalive_thread.daemon = True

        self.state = 'init'
        timer = threading.Timer(settings.vpn.startup_timeout, timeout)
        timer.daemon = True
        timer.start()

        try:
            self.resources_acquire()

            cursor_id = self.get_cursor_id()

            if self.is_interrupted():
                return

            self.state = 'temp_path'
            os.makedirs(self._temp_path)

            if self.is_interrupted():
                return

            self.state = 'ip_forwarding'
            self.enable_ip_forwarding()

            if self.is_interrupted():
                return

            self.state = 'bridge_start'
            self.bridge_start()

            if self.is_interrupted():
                return

            if self.server.replicating and self.server.vxlan:
                try:
                    self.state = 'get_vxlan'
                    self.vxlan = vxlan.get_vxlan(self.server.id, self.id,
                        self.server.ipv6)

                    if self.is_interrupted():
                        return

                    self.state = 'start_vxlan'
                    self.vxlan.start()

                    if self.is_interrupted():
                        return
                except:
                    logger.exception('Failed to setup server vxlan', 'vxlan',
                        server_id=self.server.id,
                        instance_id=self.id,
                    )

            self.state = 'generate_ovpn_conf'
            self.generate_ovpn_conf()

            if self.is_interrupted():
                return

            self.state = 'generate_iptables_rules'
            self.generate_iptables_rules()

            if self.server.wg:
                self.state = 'generate_iptables_rules_wg'
                self.generate_iptables_rules_wg()

            if self.is_interrupted():
                return

            self.state = 'publish'
            self.publish('started')

            if self.is_interrupted():
                return

            self.state = 'startup_keepalive'
            startup_keepalive_thread.start()

            if self.is_interrupted():
                return

            self.state = 'upsert_iptables_rules'
            self.iptables.upsert_rules()

            if self.server.wg:
                self.state = 'upsert_iptables_rules_wg'
                self.iptables_wg.upsert_rules()

            if self.is_interrupted():
                return

            self.state = 'init_route_advertisements'
            self.init_route_advertisements()

            if self.is_interrupted():
                return

            self.state = 'openvpn_start'
            self.process = self.openvpn_start()
            self.start_threads(cursor_id)

            if self.is_interrupted():
                return

            self.state = 'instance_com_start'
            self.instance_com = ServerInstanceCom(self.server, self)
            self.instance_com.start()

            if self.is_interrupted():
                return

            if send_events:
                self.state = 'events'
                event.Event(type=SERVERS_UPDATED)
                event.Event(type=SERVER_HOSTS_UPDATED,
                    resource_id=self.server.id)
                for org_id in self.server.organizations:
                    event.Event(type=USERS_UPDATED, resource_id=org_id)

                    if self.is_interrupted():
                        return

            for link_doc in self.server.links:
                if self.server.id > link_doc['server_id']:
                    linked_server = get_by_id(link_doc['server_id'])
                    if not linked_server:
                        continue

                    self.state = 'instance_link'
                    instance_link = ServerInstanceLink(
                        server=self.server,
                        linked_server=linked_server,
                    )
                    self.server_links.append(instance_link)
                    instance_link.start()

                    if self.is_interrupted():
                        return

            if self.server.wg:
                self.state = 'start_wg'
                self.start_wg()

            self.state = 'running'
            self.openvpn_output()

            if self.is_interrupted():
                return

            timer.cancel()
            self.startup_interrupt = True

            plugins.caller(
                'server_start',
                host_id=settings.local.host_id,
                host_name=settings.local.host.name,
                server_id=self.server.id,
                server_name=self.server.name,
                port=self.server.port,
                protocol=self.server.protocol,
                ipv6=self.server.ipv6,
                ipv6_firewall=self.server.ipv6_firewall,
                network=self.server.network,
                network6=self.server.network6,
                network_mode=self.server.network_mode,
                network_start=self.server.network_start,
                network_stop=self.server.network_end,
                restrict_routes=self.server.restrict_routes,
                bind_address=self.server.bind_address,
                onc_hostname=None,
                dh_param_bits=self.server.dh_param_bits,
                multi_device=self.server.multi_device,
                dns_servers=self.server.dns_servers,
                search_domain=self.server.search_domain,
                otp_auth=self.server.otp_auth,
                cipher=self.server.cipher,
                hash=self.server.hash,
                inter_client=self.server.inter_client,
                ping_interval=self.server.ping_interval,
                ping_timeout=self.server.ping_timeout,
                link_ping_interval=self.server.link_ping_interval,
                link_ping_timeout=self.server.link_ping_timeout,
                allowed_devices=self.server.allowed_devices,
                max_clients=self.server.max_clients,
                replica_count=self.server.replica_count,
                dns_mapping=self.server.dns_mapping,
                debug=self.server.debug,
                interface=self.interface,
                bridge_interface=self.bridge_interface,
                vxlan=self.vxlan,
            )
            try:
                while True:
                    if self.process.poll() is not None:
                        break
                    if self.is_interrupted():
                        self.stop_process()
                    time.sleep(0.05)
            finally:
                plugins.caller(
                    'server_stop',
                    host_id=settings.local.host_id,
                    host_name=settings.local.host.name,
                    server_id=self.server.id,
                    server_name=self.server.name,
                    port=self.server.port,
                    protocol=self.server.protocol,
                    ipv6=self.server.ipv6,
                    ipv6_firewall=self.server.ipv6_firewall,
                    network=self.server.network,
                    network6=self.server.network6,
                    network_mode=self.server.network_mode,
                    network_start=self.server.network_start,
                    network_stop=self.server.network_end,
                    restrict_routes=self.server.restrict_routes,
                    bind_address=self.server.bind_address,
                    onc_hostname=None,
                    dh_param_bits=self.server.dh_param_bits,
                    multi_device=self.server.multi_device,
                    dns_servers=self.server.dns_servers,
                    search_domain=self.server.search_domain,
                    otp_auth=self.server.otp_auth,
                    cipher=self.server.cipher,
                    hash=self.server.hash,
                    inter_client=self.server.inter_client,
                    ping_interval=self.server.ping_interval,
                    ping_timeout=self.server.ping_timeout,
                    link_ping_interval=self.server.link_ping_interval,
                    link_ping_timeout=self.server.link_ping_timeout,
                    allowed_devices=self.server.allowed_devices,
                    max_clients=self.server.max_clients,
                    replica_count=self.server.replica_count,
                    dns_mapping=self.server.dns_mapping,
                    debug=self.server.debug,
                    interface=self.interface,
                    bridge_interface=self.bridge_interface,
                    vxlan=self.vxlan,
                )

            if not self.clean_exit:
                event.Event(type=SERVERS_UPDATED)
                self.server.send_link_events()
                logger.LogEntry(
                    message='Server stopped unexpectedly "%s".' % (
                        self.server.name))
        except:
            try:
                self.stop_process()
            except:
                logger.exception('Server stop error', 'server',
                    server_id=self.server.id,
                    instance_id=self.id,
                )

            logger.exception('Server error occurred while running', 'server',
                server_id=self.server.id,
                instance_id=self.id,
            )
        finally:
            timer.cancel()
            self.startup_interrupt = True

            self.interrupt = True
            self.sock_interrupt = True

            try:
                self.bridge_stop()
            except:
                logger.exception('Failed to remove server bridge', 'server',
                    server_id=self.server.id,
                    instance_id=self.id,
                )

            try:
                self.iptables.clear_rules()
            except:
                logger.exception('Server iptables clean up error', 'server',
                    server_id=self.server.id,
                    instance_id=self.id,
                )

            try:
                if self.server.wg:
                    self.iptables_wg.clear_rules()
            except:
                logger.exception('Server iptables clean up error', 'server',
                    server_id=self.server.id,
                    instance_id=self.id,
                )

            if self.vxlan:
                try:
                    self.vxlan.stop()
                except:
                    logger.exception('Failed to stop server vxlan', 'server',
                        server_id=self.server.id,
                        instance_id=self.id,
                    )

            try:
                if self.server.wg:
                    self.stop_wg()
            except:
                logger.exception('Server wg clean up error', 'server',
                    server_id=self.server.id,
                    instance_id=self.id,
                )

            try:
                self.collection.update({
                    '_id': self.server.id,
                    'instances.instance_id': self.id,
                }, {
                    '$pull': {
                        'instances': {
                            'instance_id': self.id,
                        },
                    },
                    '$inc': {
                        'instances_count': -1,
                    },
                })
                utils.rmtree(self._temp_path)
            except:
                logger.exception('Server clean up error', 'server',
                    server_id=self.server.id,
                    instance_id=self.id,
                )

            try:
                self.resources_release()
            except:
                logger.exception('Failed to release resources', 'server',
                    server_id=self.server.id,
                    instance_id=self.id,
                )

    def run(self, send_events=False):
        availability_group = settings.local.host.availability_group

        response = self.collection.update({
            '_id': self.server.id,
            'status': ONLINE,
            'instances_count': {'$lt': self.server.replica_count},
            '$or': [
                {'availability_group': None},
                {'availability_group': {'$exists': False}},
                {'availability_group': availability_group},
            ],
        }, {
            '$set': {
                'availability_group': availability_group,
            },
            '$push': {
                'instances': {
                    'instance_id': self.id,
                    'host_id': settings.local.host_id,
                    'ping_timestamp': utils.now() + \
                        datetime.timedelta(seconds=30),
                },
            },
            '$inc': {
                'instances_count': 1,
            },
        })

        if not response['updatedExisting']:
            return

        threading.Thread(target=self._run_thread, args=(send_events,)).start()

def get_instance(server_id):
    try:
        return _instances[server_id]
    except KeyError:
        return
