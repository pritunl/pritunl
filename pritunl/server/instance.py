from pritunl.server.output import ServerOutput
from pritunl.server.bandwidth import ServerBandwidth
from pritunl.server.ip_pool import ServerIpPool
from pritunl.server.instance_link import ServerInstanceLink

from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *
from pritunl import settings
from pritunl import ipaddress
from pritunl import logger
from pritunl import host
from pritunl import utils
from pritunl import mongo
from pritunl import queue
from pritunl import transaction
from pritunl import event
from pritunl import messenger
from pritunl import organization
from pritunl import listener

import os
import signal
import time
import datetime
import subprocess
import threading
import traceback
import re
import bson
import pymongo
import random
import collections
import select

_resource_locks = collections.defaultdict(threading.Lock)

class ServerInstance(object):
    def __init__(self, server):
        self.server = server
        self.instance_id = bson.ObjectId()
        self.resource_lock = None
        self.interrupt = False
        self.clean_exit = False
        self.clients = {}
        self.cur_clients = set()
        self.ignore_clients = set()
        self.client_count = 0
        self.interface = None
        self.primary_user = None
        self.process = None
        self.iptables_rules = []
        self.replica_links = {}
        self.server_links = []
        self._temp_path = utils.get_temp_path()

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
        self.interface = utils.tun_interface_acquire()

    def resources_release(self):
        if self.resource_lock:
            self.resource_lock.release()
            utils.tun_interface_release(self.interface)
            self.interface = None

    def generate_ovpn_conf(self):
        # TODO
        from pritunl.server.utils import get_server

        logger.debug('Generating server ovpn conf. %r' % {
            'server_id': self.server.id,
        })

        if not self.server.primary_organization or \
                not self.server.primary_user:
            self.server.create_primary_user()

        primary_org = organization.get_org(
            id=self.server.primary_organization)
        if not primary_org:
            self.server.create_primary_user()
            primary_org = organization.get_org(
                id=self.server.primary_organization)

        self.primary_user = primary_org.get_user(self.server.primary_user)
        if not self.primary_user:
            self.server.create_primary_user()
            primary_org = organization.get_org(
                id=self.server.primary_organization)
            self.primary_user = primary_org.get_user(self.server.primary_user)

        tls_verify_path = os.path.join(self._temp_path,
            TLS_VERIFY_NAME)
        user_pass_verify_path = os.path.join(self._temp_path,
            USER_PASS_VERIFY_NAME)
        client_connect_path = os.path.join(self._temp_path,
            CLIENT_CONNECT_NAME)
        client_disconnect_path = os.path.join(self._temp_path,
            CLIENT_DISCONNECT_NAME)
        ovpn_status_path = os.path.join(self._temp_path,
            OVPN_STATUS_NAME)
        ovpn_conf_path = os.path.join(self._temp_path,
            OVPN_CONF_NAME)

        auth_host = settings.conf.bind_addr
        if auth_host == '0.0.0.0':
            auth_host = 'localhost'
        for script, script_path in (
                    (TLS_VERIFY_SCRIPT, tls_verify_path),
                    (USER_PASS_VERIFY_SCRIPT, user_pass_verify_path),
                    (CLIENT_CONNECT_SCRIPT, client_connect_path),
                    (CLIENT_DISCONNECT_SCRIPT, client_disconnect_path),
                ):
            with open(script_path, 'w') as script_file:
                os.chmod(script_path, 0755) # TODO
                script_file.write(script % (
                    settings.app.server_api_key,
                    '/dev/null', # TODO
                    'https' if settings.conf.ssl else 'http',
                    auth_host,
                    settings.conf.port,
                    self.server.id,
                ))

        push = ''
        if self.server.mode == LOCAL_TRAFFIC:
            for network in self.server.local_networks:
                push += 'push "route %s %s"\n' % utils.parse_network(network)
        elif self.server.mode == VPN_TRAFFIC:
            pass
        else:
            push += 'push "redirect-gateway"\n'
        for dns_server in self.server.dns_servers:
            push += 'push "dhcp-option DNS %s"\n' % dns_server
        if self.server.search_domain:
            push += 'push "dhcp-option DOMAIN %s"\n' % (
                self.server.search_domain)

        for link_svr_id in self.server.links.iterkeys():
            link_svr = get_server(id=link_svr_id)
            push += 'push "route %s %s"\n' % utils.parse_network(
                link_svr.network)
            for local_network in link_svr.local_networks:
                push += 'push "route %s %s"\n' % utils.parse_network(
                    local_network)

        server_conf = OVPN_INLINE_SERVER_CONF % (
            self.server.port,
            self.server.protocol,
            self.interface,
            tls_verify_path,
            client_connect_path,
            client_disconnect_path,
            '%s %s' % utils.parse_network(self.server.network),
            ovpn_status_path,
            4 if self.server.debug else 1,
            8 if self.server.debug else 3,
        )

        if self.server.otp_auth:
            server_conf += 'auth-user-pass-verify %s via-file\n' % (
                user_pass_verify_path)

        # Pritunl v0.10.x did not include comp-lzo in client conf
        # if lzo_compression is adaptive dont include comp-lzo in server conf
        if self.server.lzo_compression == ADAPTIVE:
            pass
        elif self.server.lzo_compression:
            server_conf += 'comp-lzo yes\npush "comp-lzo yes"\n'
        else:
            server_conf += 'comp-lzo no\npush "comp-lzo no"\n'

        if self.server.mode in (LOCAL_TRAFFIC, VPN_TRAFFIC):
            server_conf += 'client-to-client\n'

        server_conf += PERF_MODES[self.server.performance_mode]

        if push:
            server_conf += push

        server_conf += '<ca>\n%s\n</ca>\n' % utils.get_cert_block(
            self.server.ca_certificate)
        server_conf += '<cert>\n%s\n</cert>\n' % utils.get_cert_block(
            self.primary_user.certificate)
        server_conf += '<key>\n%s\n</key>\n' % self.primary_user.private_key
        server_conf += '<dh>\n%s\n</dh>\n' % self.server.dh_params

        with open(ovpn_conf_path, 'w') as ovpn_conf:
            os.chmod(ovpn_conf_path, 0600)
            ovpn_conf.write(server_conf)

    def enable_ip_forwarding(self):
        logger.debug('Enabling ip forwarding. %r' % {
            'server_id': self.server.id,
        })

        try:
            subprocess.check_call(['sysctl', '-w', 'net.ipv4.ip_forward=1'],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError:
            logger.exception('Failed to enable IP forwarding. %r' % {
                'server_id': self.server.id,
            })
            raise

    def generate_iptables_rules(self):
        rules = []

        try:
            routes_output = subprocess.check_output(['route', '-n'],
                stderr=subprocess.PIPE)
        except subprocess.CalledProcessError:
            logger.exception('Failed to get IP routes. %r' % {
                'server_id': self.server.id,
            })
            raise

        routes = {}
        for line in routes_output.splitlines():
            line_split = line.split()
            if len(line_split) < 8 or not re.match(IP_REGEX, line_split[0]):
                continue
            routes[line_split[0]] = line_split[7]

        if '0.0.0.0' not in routes:
            raise IptablesError('Failed to find default network interface', {
                'server_id': self.server.id,
            })
        default_interface = routes['0.0.0.0']

        rules.append(['INPUT', '-i', self.interface, '-j', 'ACCEPT'])
        rules.append(['FORWARD', '-i', self.interface, '-j', 'ACCEPT'])

        interfaces = set()
        for network_address in self.server.local_networks or ['0.0.0.0/0']:
            args = ['POSTROUTING', '-t', 'nat']
            network = utils.parse_network(network_address)[0]

            if network not in routes:
                logger.debug('Failed to find interface for local network ' + \
                        'route, using default route. %r' % {
                    'server_id': self.server.id,
                })
                interface = default_interface
            else:
                interface = routes[network]
            interfaces.add(interface)

            if network != '0.0.0.0':
                args += ['-d', network_address]

            args += [
                '-s', self.server.network,
                '-o', interface,
                '-j', 'MASQUERADE',
            ]
            rules.append(args)

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

        extra_args = [
            '--wait',
            '-m', 'comment',
            '--comment', 'pritunl_%s' % self.server.id,
        ]
        rules = [x + extra_args for x in rules]

        return rules

    def exists_iptables_rules(self, rule):
        cmd = ['iptables', '-C'] + rule
        return (cmd, subprocess.Popen(cmd,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE))

    def set_iptables_rules(self):
        logger.debug('Setting iptables rules. %r' % {
            'server_id': self.server.id,
        })

        processes = {}
        poller = select.epoll()
        self.iptables_rules = self.generate_iptables_rules()

        for rule in self.iptables_rules:
            cmd, process = self.exists_iptables_rules(rule)
            fileno = process.stdout.fileno()

            processes[fileno] = (cmd, process, ['iptables', '-A'] + rule)
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
                'routing rule. %r' % {
                    'server_id': self.server.id,
                    'rule': rule,
                    'output': error.output,
                })
            raise

    def clear_iptables_rules(self):
        logger.debug('Clearing iptables rules. %r' % {
            'server_id': self.server.id,
        })

        processes = []

        for rule in self.iptables_rules:
            process = subprocess.Popen(['iptables', '-D'] + rule,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            processes.append(process)

        for process in processes:
            process.wait()

    def update_clients_bandwidth(self, clients):
        # Remove client no longer connected
        for client_id in self.clients.keys():
            if client_id not in clients:
                del self.clients[client_id]

        # Get total bytes send and recv for all clients
        bytes_recv_t = 0
        bytes_sent_t = 0
        for client_id in clients:
            bytes_recv = clients[client_id]['bytes_received']
            bytes_sent = clients[client_id]['bytes_sent']
            prev_bytes_recv, prev_bytes_sent = self.clients.get(
                client_id, (0, 0))
            self.clients[client_id] = (bytes_recv, bytes_sent)

            if prev_bytes_recv > bytes_recv or prev_bytes_sent > bytes_sent:
                prev_bytes_recv = 0
                prev_bytes_sent = 0

            bytes_recv_t += bytes_recv - prev_bytes_recv
            bytes_sent_t += bytes_sent - prev_bytes_sent

        if bytes_recv_t != 0 or bytes_sent_t != 0:
            self.server.bandwidth.add_data(
                utils.now(), bytes_recv_t, bytes_sent_t)

    def update_clients(self, clients_str):
        # Openvpn will create an undef client while a client connects
        clients_str.pop('UNDEF', None)
        clients = {}

        for client_id in clients_str:
            clients[bson.ObjectId(client_id)] = clients_str[client_id]

        new_clients_set = set(clients)

        new_clients = new_clients_set - self.cur_clients
        if new_clients:
            cursor = self.user_collection.find({
                '_id': {'$in': new_clients},
            }, {
                'type': True,
            })

            for doc in cursor:
                if doc['type'] != CERT_CLIENT:
                    self.ignore_clients.add(doc['_id'])

        rem_clients = self.cur_clients - new_clients_set
        for client_id in rem_clients:
            self.cur_clients.remove(client_id)
            if client_id in self.ignore_clients:
                self.ignore_clients.remove(client_id)

        for client_id in self.ignore_clients:
            clients.pop(client_id, None)

        response = self.collection.update({
            '_id': self.server.id,
            'instances.instance_id': self.instance_id,
        }, {'$set': {
            'instances.$.clients': clients,
        }})

        if not response['updatedExisting']:
            return

        self.update_clients_bandwidth(clients)

        if self.client_count != len(clients):
            for org_id in self.server.organizations:
                event.Event(type=USERS_UPDATED, resource_id=org_id)
            event.Event(type=SERVERS_UPDATED)
            self.client_count = len(clients)

    def read_clients(self):
        path = os.path.join(self._temp_path, OVPN_STATUS_NAME)
        clients = {}

        if os.path.isfile(path):
            with open(path, 'r') as status_file:
                for line in status_file.readlines():
                    if line[:11] != 'CLIENT_LIST':
                        continue
                    line_split = line.strip('\n').split(',')
                    client_id = line_split[1]
                    real_address = line_split[2]
                    virt_address = line_split[3]
                    bytes_recv = line_split[4]
                    bytes_sent = line_split[5]
                    connected_since = line_split[7]
                    clients[client_id] = {
                        'real_address': real_address,
                        'virt_address': virt_address,
                        'bytes_received': int(bytes_recv),
                        'bytes_sent': int(bytes_sent),
                        'connected_since': int(connected_since),
                    }
        self.update_clients(clients)

    def stop_process(self):
        terminated = utils.stop_process(self.process)

        if not terminated:
            logger.error('Failed to stop server process. %r' % {
                'server_id': self.server.id,
                'instance_id': self.instance_id,
            })
            return False

        return terminated

    def openvpn_start(self):
        ovpn_conf_path = os.path.join(self._temp_path, OVPN_CONF_NAME)

        try:
            return subprocess.Popen(['openvpn', ovpn_conf_path],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except OSError:
            self.server.output.push_output(traceback.format_exc())
            logger.exception('Failed to start ovpn process. %r' % {
                'server_id': self.server.id,
            })
            self.publish('error')

    def openvpn_watch(self):
        while True:
            line = self.process.stdout.readline()
            if not line:
                if self.process.poll() is not None:
                    break
                else:
                    time.sleep(0.05)
                    continue

            try:
                self.server.output.push_output(line)
            except:
                logger.exception('Failed to push vpn output. %r', {
                    'server_id': self.server.id,
                })

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
        finally:
            self.stop_process()

    def _status_thread(self):
        while not self.interrupt:
            self.read_clients()
            time.sleep(settings.vpn.status_update_rate)

    def link_instance(self, host_id):
        if self.interrupt:
            return
        instance_link = ServerInstanceLink(
            server=self.server,
            linked_server=self.server,
            linked_host=host.get_host(id=host_id),
        )
        self.replica_links[host_id] = instance_link
        instance_link.start()

    def _keep_alive_thread(self):
        exit_attempts = 0

        while not self.interrupt:
            try:
                doc = self.collection.find_and_modify({
                    '_id': self.server.id,
                    'instances.instance_id': self.instance_id,
                }, {'$set': {
                    'instances.$.ping_timestamp': utils.now(),
                }}, fields={
                    '_id': False,
                    'instances': True,
                })

                if not doc:
                    if self.stop_process():
                        break
                    else:
                        time.sleep(0.1)
                        continue

                active_hosts = set()
                for instance in doc['instances']:
                    host_id = instance['host_id']

                    if host_id == settings.local.host_id:
                        continue
                    active_hosts.add(host_id)

                    if host_id not in self.replica_links:
                        self.link_instance(host_id)

                for host_id in self.replica_links.keys():
                    if host_id not in active_hosts:
                        self.replica_links[host_id].stop()
                        del self.replica_links[host_id]
            except:
                logger.exception('Failed to update server ping. %r' % {
                    'server_id': self.server.id,
                })
            time.sleep(settings.vpn.server_ping)

    def start_threads(self, cursor_id):
        thread = threading.Thread(target=self._sub_thread, args=(cursor_id,))
        thread.daemon = True
        thread.start()

        thread = threading.Thread(target=self._status_thread)
        thread.daemon = True
        thread.start()

        thread = threading.Thread(target=self._keep_alive_thread)
        thread.daemon = True
        thread.start()

    def _run_thread(self, send_events):
        from pritunl.server.utils import get_server

        logger.debug('Starting ovpn process. %r' % {
            'server_id': self.server.id,
        })

        self.resources_acquire()
        try:
            cursor_id = self.get_cursor_id()

            os.makedirs(self._temp_path)
            ovpn_conf_path = self.generate_ovpn_conf()

            self.enable_ip_forwarding()
            self.set_iptables_rules()

            self.process = self.openvpn_start()
            if not self.process:
                return

            self.start_threads(cursor_id)

            self.publish('started')

            for link_svr_id in self.server.links:
                if self.server.id > link_svr_id:
                    instance_link = ServerInstanceLink(
                        server=self.server,
                        linked_server=get_server(id=link_svr_id),
                    )
                    self.server_links.append(instance_link)
                    instance_link.start()

            if send_events:
                event.Event(type=SERVERS_UPDATED)
                event.Event(type=SERVER_HOSTS_UPDATED,
                    resource_id=self.server.id)
                for org_id in self.server.organizations:
                    event.Event(type=USERS_UPDATED, resource_id=org_id)

            self.openvpn_watch()

            self.interrupt = True
            self.clear_iptables_rules()
            self.resources_release()

            if not self.clean_exit:
                event.Event(type=SERVERS_UPDATED)
                logger.LogEntry(message='Server stopped unexpectedly "%s".' % (
                    self.server.name))
        except:
            self.interrupt = True
            if self.resource_lock:
                self.clear_iptables_rules()
            self.resources_release()

            logger.exception('Server error occurred while running. %r', {
                'server_id': self.server.id,
            })
        finally:
            for instance in self.replica_links.values() + self.server_links:
                instance.stop()

            self.collection.update({
                '_id': self.server.id,
                'instances.instance_id': self.instance_id,
            }, {
                '$pull': {
                    'instances': {
                        'instance_id': self.instance_id,
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
            'status': True,
            'instances_count': {'$lt': self.server.replica_count},
        }, {
            '$push': {
                'instances': {
                    'instance_id': self.instance_id,
                    'host_id': settings.local.host_id,
                    'ping_timestamp': utils.now(),
                    'clients': {},
                },
            },
            '$inc': {
                'instances_count': 1,
            },
        })

        if not response['updatedExisting']:
            return

        thread = threading.Thread(target=self._run_thread, args=(send_events,))
        thread.start()
