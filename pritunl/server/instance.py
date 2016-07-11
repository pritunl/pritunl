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

import os
import signal
import time
import subprocess
import threading
import traceback
import re
import collections
import pymongo

_resource_locks = collections.defaultdict(threading.Lock)

class ServerInstance(object):
    def __init__(self, server):
        self.server = server
        self.id = utils.ObjectId()
        self.resource_lock = None
        self.interrupt = False
        self.sock_interrupt = False
        self.clean_exit = False
        self.interface = None
        self.bridge_interface = None
        self.primary_user = None
        self.process = None
        self.auth_log_process = None
        self.iptables = iptables.Iptables()
        self.iptables_lock = threading.Lock()
        self.tun_nat = False
        self.server_links = []
        self.route_advertisements = set()
        self._temp_path = utils.get_temp_path()
        self.ovpn_conf_path = os.path.join(self._temp_path,
            OVPN_CONF_NAME)
        self.management_socket_path = os.path.join(settings.conf.var_run_path,
            MANAGEMENT_SOCKET_NAME % self.id)

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

    def is_sock_interrupt(self):
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
        if self.resource_lock:
            raise TypeError('Server resource lock already set')
        self.resource_lock = _resource_locks[self.server.id]
        self.resource_lock.acquire()
        self.interface = utils.interface_acquire(self.server.adapter_type)

    def resources_release(self):
        if self.resource_lock:
            self.resource_lock.release()
            utils.interface_release(self.server.adapter_type, self.interface)
            self.interface = None

    def generate_ovpn_conf(self):
        logger.debug('Generating server ovpn conf', 'server',
            server_id=self.server.id,
        )

        if not self.server.primary_organization or \
                not self.server.primary_user:
            self.server.create_primary_user()

        if self.server.primary_organization not in self.server.organizations:
            self.server.remove_primary_user()
            self.server.create_primary_user()

        primary_org = organization.get_by_id(self.server.primary_organization)
        if not primary_org:
            self.server.create_primary_user()
            primary_org = organization.get_by_id(
                id=self.server.primary_organization)

        self.primary_user = primary_org.get_user(self.server.primary_user)
        if not self.primary_user:
            self.server.create_primary_user()
            primary_org = organization.get_by_id(
                id=self.server.primary_organization)
            self.primary_user = primary_org.get_user(self.server.primary_user)

        gateway = utils.get_network_gateway(self.server.network)
        gateway6 = utils.get_network_gateway(self.server.network6)

        push = ''
        routes = []
        for route in self.server.get_routes(include_default=False):
            routes.append(route['network'])
            if route['virtual_network']:
                continue

            network = route['network']
            if not route.get('network_link'):
                if ':' in network:
                    push += 'push "route-ipv6 %s "\n' % network
                else:
                    push += 'push "route %s %s"\n' % utils.parse_network(
                        network)
            else:
                if ':' in network:
                    push += 'route-ipv6 %s %s\n' % (network, gateway6)
                else:
                    push += 'route %s %s %s\n' % (utils.parse_network(
                        network) + (gateway,))

        for link_svr in self.server.iter_links(fields=(
                '_id', 'network', 'local_networks', 'network_start',
                'network_end', 'organizations', 'routes', 'links', 'ipv6')):
            if self.server.id < link_svr.id:
                for route in link_svr.get_routes(include_default=False):
                    network = route['network']
                    if ':' in network:
                        push += 'route-ipv6 %s %s\n' % (
                            network, gateway6)
                    else:
                        push += 'route %s %s %s\n' % (utils.parse_network(
                            network) + (gateway,))

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
            if self.server.ipv6 or settings.vpn.ipv6:
                protocol = 'tcp6-server'
            else:
                protocol = 'tcp-server'
        elif self.server.protocol == 'udp':
            if self.server.ipv6 or settings.vpn.ipv6:
                protocol = 'udp6'
            else:
                protocol = 'udp'
        else:
            raise ValueError('Unknown protocol')

        server_conf = OVPN_INLINE_SERVER_CONF % (
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
            CIPHERS[self.server.cipher],
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

        if settings.local.sub_plan == 'enterprise':
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
                onc_hostname=self.server.onc_hostname,
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
                max_clients=self.server.max_clients,
                replica_count=self.server.replica_count,
                dns_mapping=self.server.dns_mapping,
                debug=self.server.debug,
                routes=routes,
            )

            if returns:
                for return_val in returns:
                    if not return_val:
                        continue
                    server_conf += return_val.strip() + '/n'

        server_conf += '<ca>\n%s\n</ca>\n' % self.server.ca_certificate

        if self.server.tls_auth:
            server_conf += 'key-direction 0\n<tls-auth>\n%s\n</tls-auth>\n' % (
                self.server.tls_auth_key)

        server_conf += '<cert>\n%s\n</cert>\n' % utils.get_cert_block(
            self.primary_user.certificate)
        server_conf += '<key>\n%s\n</key>\n' % self.primary_user.private_key
        server_conf += '<dh>\n%s\n</dh>\n' % self.server.dh_params

        with open(self.ovpn_conf_path, 'w') as ovpn_conf:
            os.chmod(self.ovpn_conf_path, 0600)
            ovpn_conf.write(server_conf)

    def enable_ip_forwarding(self):
        logger.debug('Enabling ip forwarding', 'server',
            server_id=self.server.id,
        )

        try:
            utils.check_output_logged(
                ['sysctl', '-w', 'net.ipv4.ip_forward=1'])
        except subprocess.CalledProcessError:
            logger.exception('Failed to enable IP forwarding', 'server',
                server_id=self.server.id,
            )
            raise

        if self.server.ipv6:
            try:
                utils.check_output_logged(
                    ['sysctl', '-w', 'net.ipv6.conf.all.forwarding=1'])
            except subprocess.CalledProcessError:
                logger.exception('Failed to enable IPv6 forwarding', 'server',
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
                    ipaddress.IPNetwork('%s/%s' % (line_split[0],
                        utils.subnet_to_cidr(line_split[2]))),
                    line_split[7]
                ))
        routes.reverse()

        if not default_interface:
            raise IptablesError('Failed to find default network interface')

        routes6 = []
        default_interface6 = None
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
                    if default_interface6:
                        continue
                    default_interface6 = line_split[6]

                routes6.append((
                    route_network,
                    line_split[6],
                ))

            if not default_interface6:
                raise IptablesError(
                    'Failed to find default IPv6 network interface')

            if default_interface6 == 'lo':
                logger.error('Failed to find default IPv6 interface',
                    'server',
                    server_id=self.server.id,
                )
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

            if route['virtual_network']:
                continue

            network = route['network']
            is6 = ':' in network
            network_obj = ipaddress.IPNetwork(network)

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

            self.iptables.add_route(
                network,
                nat=route['nat'],
                nat_interface=interface,
            )

        self.iptables.generate()

    def enable_iptables_tun_nat(self):
        # TODO
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
                '-m', 'comment',
                '--comment', 'pritunl_%s' % self.server.id,
            ]
            self.iptables.add_rule(rule)
            self.iptables.add_rule6(rule)
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
            self.server.output.push_output(traceback.format_exc())
            logger.exception('Failed to start ovpn process', 'server',
                server_id=self.server.id,
            )
            self.publish('error')

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
    def openvpn_watch(self):
        while True:
            line = self.process.stdout.readline()
            if not line:
                if self.process.poll() is not None:
                    break
                else:
                    time.sleep(0.05)
                    continue

            yield

            try:
                self.server.output.push_output(line)
            except:
                logger.exception('Failed to push vpn output', 'server',
                    server_id=self.server.id,
                )

            yield

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
                        self.clean_exit = True
                        for _ in xrange(10):
                            self.process.send_signal(signal.SIGKILL)
                            time.sleep(0.01)
                except OSError:
                    pass
        except:
            logger.exception('Exception in messaging thread', 'server',
                server_id=self.server.id,
            )
            self.stop_process()

    @interrupter
    def _keep_alive_thread(self):
        try:
            while not self.interrupt:
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
                        logger.error(
                            'Instance doc lost, stopping server', 'server',
                            server_id=self.server.id,
                        )

                        if self.stop_process():
                            break
                        else:
                            time.sleep(0.1)
                            continue

                    yield
                except:
                    logger.exception('Failed to update server ping', 'server',
                        server_id=self.server.id,
                    )
                    time.sleep(1)

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
            vpc_region = route['vpc_region']
            vpc_id = route['vpc_id']
            network = route['network']

            if vpc_region and vpc_id:
                self.reserve_route_advertisement(
                    vpc_region, vpc_id, network)

    def clear_route_advertisements(self):
        for ra_id in self.route_advertisements.copy():
            self.routes_collection.remove({
                '_id': ra_id,
            })

    def reserve_route_advertisement(self, vpc_region, vpc_id, network):
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

            utils.add_vpc_route(vpc_region, vpc_id, network,
                settings.local.host.aws_id)

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

    def stop_threads(self):
        if self.auth_log_process:
            try:
                self.auth_log_process.send_signal(signal.SIGINT)
            except OSError as error:
                if error.errno != 3:
                    raise

    def _run_thread(self, send_events):
        from pritunl.server.utils import get_by_id

        logger.debug('Starting ovpn process', 'server',
            server_id=self.server.id,
        )

        self.resources_acquire()
        try:
            cursor_id = self.get_cursor_id()

            os.makedirs(self._temp_path)

            self.enable_ip_forwarding()
            self.bridge_start()
            self.generate_ovpn_conf()

            self.generate_iptables_rules()
            self.iptables.upsert_rules()

            self.init_route_advertisements()

            self.process = self.openvpn_start()
            if not self.process:
                return

            self.start_threads(cursor_id)

            self.instance_com = ServerInstanceCom(self.server, self)
            self.instance_com.start()

            self.publish('started')

            if send_events:
                event.Event(type=SERVERS_UPDATED)
                event.Event(type=SERVER_HOSTS_UPDATED,
                    resource_id=self.server.id)
                for org_id in self.server.organizations:
                    event.Event(type=USERS_UPDATED, resource_id=org_id)

            for link_doc in self.server.links:
                if self.server.id > link_doc['server_id']:
                    instance_link = ServerInstanceLink(
                        server=self.server,
                        linked_server=get_by_id(link_doc['server_id']),
                    )
                    self.server_links.append(instance_link)
                    instance_link.start()

            self.openvpn_watch()

            self.interrupt = True
            self.bridge_stop()
            self.iptables.clear_rules()
            self.resources_release()

            if not self.clean_exit:
                event.Event(type=SERVERS_UPDATED)
                self.server.send_link_events()
                logger.LogEntry(
                    message='Server stopped unexpectedly "%s".' % (
                        self.server.name))
        except:
            self.interrupt = True
            self.stop_process()
            if self.resource_lock:
                self.iptables.clear_rules()
                self.bridge_stop()
            self.resources_release()

            logger.exception('Server error occurred while running', 'server',
                server_id=self.server.id,
            )
        finally:
            self.stop_threads()
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

    def run(self, send_events=False):
        response = self.collection.update({
            '_id': self.server.id,
            'status': ONLINE,
            'instances_count': {'$lt': self.server.replica_count},
        }, {
            '$push': {
                'instances': {
                    'instance_id': self.id,
                    'host_id': settings.local.host_id,
                    'ping_timestamp': utils.now(),
                },
            },
            '$inc': {
                'instances_count': 1,
            },
        })

        if not response['updatedExisting']:
            return

        threading.Thread(target=self._run_thread, args=(send_events,)).start()
