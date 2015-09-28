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
from pritunl import ipaddress

import os
import signal
import time
import subprocess
import threading
import traceback
import re
import collections
import select

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
        self.iptables_rules = []
        self.ip6tables_rules = []
        self.server_links = []
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

    def get_cursor_id(self):
        return messenger.get_cursor_id('servers')

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

        push = ''
        if self.server.mode == LOCAL_TRAFFIC:
            for network in self.server.local_networks:
                push += 'push "route %s %s"\n' % utils.parse_network(network)
        elif self.server.mode == VPN_TRAFFIC:
            pass

        for link_svr in self.server.iter_links(fields=(
                '_id', 'network', 'local_networks', 'network_start',
                'network_end')):
            if self.server.id < link_svr.id:
                gateway = utils.get_network_gateway(self.server.network)
                push += 'route %s %s %s\n' % (utils.parse_network(
                    link_svr.network) + (gateway,))
                for local_network in link_svr.local_networks:
                    push += 'route %s %s %s\n' % (utils.parse_network(
                        local_network) + (gateway,))

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

        server_conf = OVPN_INLINE_SERVER_CONF % (
            self.server.port,
            self.server.protocol + '6' if self.server.ipv6 else '',
            self.interface,
            server_line,
            self.management_socket_path,
            self.server.max_clients,
            self.server.ping_interval,
            self.server.ping_timeout + 20,
            self.server.ping_interval,
            self.server.ping_timeout,
            CIPHERS[self.server.cipher],
            4 if self.server.debug else 1,
            8 if self.server.debug else 3,
        )

        if self.server.bind_address:
            server_conf += 'local %s\n' % self.server.bind_address

        if self.server.inter_client:
            server_conf += 'client-to-client\n'

        if self.server.multi_device:
            server_conf += 'duplicate-cn\n'

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
        rules = []
        rules6 = []

        try:
            routes_output = utils.check_output_logged(['route', '-n'])
        except subprocess.CalledProcessError:
            logger.exception('Failed to get IP routes', 'server',
                server_id=self.server.id,
            )
            raise

        routes = {}
        for line in routes_output.splitlines():
            line_split = line.split()
            if len(line_split) < 8 or not re.match(IP_REGEX, line_split[0]):
                continue
            if line_split[0] not in routes:
                routes[line_split[0]] = line_split[7]

        if '0.0.0.0' not in routes:
            raise IptablesError('Failed to find default network interface')
        default_interface = routes['0.0.0.0']

        routes6 = {}
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
                    ipaddress.IPv6Network(line_split[0])
                except ipaddress.AddressValueError:
                    continue

                if line_split[0] not in routes6:
                    routes6[line_split[0]] = line_split[6]

            if '::/0' not in routes6:
                raise IptablesError(
                    'Failed to find default IPv6 network interface')
            default_interface6 = routes6['::/0']

        rules.append(['INPUT', '-i', self.interface, '-j', 'ACCEPT'])
        rules.append(['FORWARD', '-i', self.interface, '-j', 'ACCEPT'])
        if self.server.ipv6:
            rules6.append(['INPUT', '-i', self.interface, '-j', 'ACCEPT'])
            rules6.append(['FORWARD', '-i', self.interface, '-j', 'ACCEPT'])

        interfaces = set()
        interfaces6 = set()
        other_networks = []
        if self.server.mode == ALL_TRAFFIC and \
                self.server.network_mode != BRIDGE:
            other_networks = ['0.0.0.0/0']
            if self.server.ipv6:
                other_networks.append('::/0')

        link_svr_networks = []
        for link_svr in self.server.iter_links(fields=('_id', 'network')):
            # TODO Add IPv6 networks
            link_svr_networks.append(link_svr.network)

        for network_address in self.server.local_networks or other_networks:
            args_base = ['POSTROUTING', '-t', 'nat']
            is6 = ':' in network_address
            if is6:
                network = network_address
            else:
                network = utils.parse_network(network_address)[0]

            if is6:
                if network not in routes6:
                    logger.info('Failed to find interface for local ' + \
                        'IPv6 network route, using default route', 'server',
                        server_id=self.server.id,
                        network=network,
                    )
                    interface = default_interface6
                else:
                    interface = routes6[network]
                interfaces6.add(interface)
            else:
                if network not in routes:
                    logger.info('Failed to find interface for local ' + \
                        'network route, using default route', 'server',
                        server_id=self.server.id,
                        network=network,
                    )
                    interface = default_interface
                else:
                    interface = routes[network]
                interfaces.add(interface)

            if network != '0.0.0.0' and network != '::/0':
                args_base += ['-d', network_address]

            args_base += [
                '-o', interface,
                '-j', 'MASQUERADE',
            ]

            if is6:
                rules6.append(args_base + ['-s', self.server.network6])
            else:
                rules.append(args_base + ['-s', self.server.network])

            for link_svr_net in link_svr_networks:
                rules.append(args_base + ['-s', link_svr_net])

        for interface in interfaces:
            rules.append([
                'FORWARD',
                '-i', interface,
                '-o', self.interface,
                '-m', 'state',
                '--state', 'ESTABLISHED,RELATED',
                '-j', 'ACCEPT',
            ])
            rules.append([
                'FORWARD',
                '-i', self.interface,
                '-o', interface,
                '-m', 'state',
                '--state', 'ESTABLISHED,RELATED',
                '-j', 'ACCEPT',
            ])

        for interface in interfaces6:
            rules6.append([
                'FORWARD',
                '-i', interface,
                '-o', self.interface,
                '-m', 'state',
                '--state', 'ESTABLISHED,RELATED',
                '-j', 'ACCEPT',
            ])
            rules6.append([
                'FORWARD',
                '-i', self.interface,
                '-o', interface,
                '-m', 'state',
                '--state', 'ESTABLISHED,RELATED',
                '-j', 'ACCEPT',
            ])

        extra_args = [
            '-m', 'comment',
            '--comment', 'pritunl_%s' % self.server.id,
        ]

        if settings.local.iptables_wait:
            extra_args.append('--wait')

        rules = [x + extra_args for x in rules]
        rules6 = [x + extra_args for x in rules6]

        return rules, rules6

    def exists_iptables_rules(self, rule):
        cmd = ['iptables', '-C'] + rule
        return (cmd, subprocess.Popen(cmd,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE))

    def exists_ip6tables_rules(self, rule):
        cmd = ['ip6tables', '-C'] + rule
        return (cmd, subprocess.Popen(cmd,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE))

    def set_iptables_rules(self):
        logger.debug('Setting iptables rules', 'server',
            server_id=self.server.id,
        )

        processes = {}
        poller = select.epoll()
        self.iptables_rules, self.ip6tables_rules = \
            self.generate_iptables_rules()

        for rule in self.iptables_rules:
            cmd, process = self.exists_iptables_rules(rule)
            fileno = process.stdout.fileno()

            processes[fileno] = (cmd, process, ['iptables', '-I'] + rule)
            poller.register(fileno, select.EPOLLHUP)

        for rule in self.ip6tables_rules:
            cmd, process = self.exists_ip6tables_rules(rule)
            fileno = process.stdout.fileno()

            processes[fileno] = (cmd, process, ['ip6tables', '-I'] + rule)
            poller.register(fileno, select.EPOLLHUP)

        try:
            while True:
                for fd, event in poller.poll(timeout=8):
                    cmd, process, next_cmd = processes.pop(fd)
                    poller.unregister(fd)

                    if next_cmd:
                        if process.poll():
                            process = subprocess.Popen(next_cmd,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                            )
                            fileno = process.stdout.fileno()

                            processes[fileno] = (next_cmd, process, None)
                            poller.register(fileno, select.EPOLLHUP)
                    else:
                        retcode = process.poll()
                        if retcode:
                            std_out, err_out = process.communicate()
                            raise subprocess.CalledProcessError(
                                retcode, cmd, output=err_out)

                    if not processes:
                        return

        except subprocess.CalledProcessError as error:
            logger.exception('Failed to apply iptables ' + \
                'routing rule', 'server',
                server_id=self.server.id,
                output=error.output,
            )
            raise

    def clear_iptables_rules(self):
        logger.debug('Clearing iptables rules', 'server',
            server_id=self.server.id,
        )

        processes = []

        for rule in self.iptables_rules:
            process = subprocess.Popen(['iptables', '-D'] + rule,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            processes.append(process)

        for rule in self.ip6tables_rules:
            process = subprocess.Popen(['ip6tables', '-D'] + rule,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            processes.append(process)

        for process in processes:
            process.wait()

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
        while not self.interrupt:
            try:
                doc = self.collection.find_and_modify({
                    '_id': self.server.id,
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

            except:
                logger.exception('Failed to update server ping', 'server',
                    server_id=self.server.id,
                )
            yield interrupter_sleep(settings.vpn.server_ping)

    def start_threads(self, cursor_id):
        thread = threading.Thread(target=self._sub_thread, args=(cursor_id,))
        thread.daemon = True
        thread.start()

        thread = threading.Thread(target=self._keep_alive_thread)
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
            self.set_iptables_rules()

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
            self.clear_iptables_rules()
            self.resources_release()

            if not self.clean_exit:
                event.Event(type=SERVERS_UPDATED)
                self.server.send_link_events()
                logger.LogEntry(message='Server stopped unexpectedly "%s".' % (
                    self.server.name))
        except:
            self.interrupt = True
            self.stop_process()
            if self.resource_lock:
                self.clear_iptables_rules()
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
