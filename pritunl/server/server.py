from pritunl.cache import cache_db

from pritunl.server.bandwidth import ServerBandwidth
from pritunl.server.ip_pool import ServerIpPool

from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
from pritunl import settings
from pritunl import app
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

import uuid
import os
import signal
import time
import datetime
import subprocess
import threading
import traceback
import re
import json
import bson
import pymongo

class Server(mongo.MongoObject):
    fields = {
        'name',
        'network',
        'network_lock',
        'interface',
        'port',
        'protocol',
        'dh_param_bits',
        'mode',
        'local_networks',
        'dns_servers',
        'search_domain',
        'public_address',
        'otp_auth',
        'lzo_compression',
        'debug',
        'organizations',
        'hosts',
        'primary_organization',
        'primary_user',
        'ca_certificate',
        'dh_params',

        'instance_id',
        'ping_timestamp',
        'status',
        'start_timestamp',
        'clients',
        'users_online',
    }
    fields_default = {
        'dns_servers': [],
        'otp_auth': False,
        'lzo_compression': False,
        'debug': False,
        'organizations': [],
        'hosts': [],
        'status': False,
        'clients': {},
        'users_online': 0,
    }
    cache_prefix = 'server'

    def __init__(self, name=None, network=None, interface=None, port=None,
            protocol=None, dh_param_bits=None, mode=None, local_networks=None,
            dns_servers=None, search_domain=None, public_address=None,
            otp_auth=None, lzo_compression=None, debug=None, **kwargs):
        mongo.MongoObject.__init__(self, **kwargs)
        self.bandwidth = ServerBandwidth(self.id)

        self._cur_event = None
        self._last_event = 0
        self._orig_network = self.network
        self._orgs_changed = False
        self._clients = None
        self._temp_path = utils.get_temp_path()
        self.ip_pool = ServerIpPool(self)

        if name is not None:
            self.name = name
        if network is not None:
            self.network = network
        if interface is not None:
            self.interface = interface
        if port is not None:
            self.port = port
        if protocol is not None:
            self.protocol = protocol
        if dh_param_bits is not None:
            self.dh_param_bits = dh_param_bits
        if mode is not None:
            self.mode = mode
        if local_networks is not None:
            self.local_networks = local_networks
        if dns_servers is not None:
            self.dns_servers = dns_servers
        if search_domain is not None:
            self.search_domain = search_domain
        if public_address is not None:
            self.public_address = public_address
        if otp_auth is not None:
            self.otp_auth = otp_auth
        if lzo_compression is not None:
            self.lzo_compression = lzo_compression
        if debug is not None:
            self.debug = debug

    @cached_static_property
    def collection(cls):
        return mongo.get_collection('servers')

    @cached_static_property
    def output_collection(cls):
        return mongo.get_collection('servers_output')

    def dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'status': self.status,
            'uptime': self.uptime,
            'users_online': len(self.clients),
            'user_count': self.user_count,
            'network': self.network,
            'interface': self.interface,
            'port': self.port,
            'protocol': self.protocol,
            'dh_param_bits': self.dh_param_bits,
            'mode': self.mode,
            'local_networks': self.local_networks,
            'dns_servers': self.dns_servers,
            'search_domain': self.search_domain,
            'public_address': self.public_address,
            'otp_auth': True if self.otp_auth else False,
            'lzo_compression': self.lzo_compression,
            'debug': True if self.debug else False,
        }

    @property
    def uptime(self):
        if not self.start_timestamp:
            return
        return max((datetime.datetime.now() - self.start_timestamp).seconds, 1)

    @cached_property
    def user_count(self):
        return organization.get_user_count_multi(org_ids=self.organizations)

    @cached_property
    def output(self):
        output = self.output_collection.aggregate([
            {'$match': {
                'server_id': self.id,
            }},
            {'$project': {
                '_id': False,
                'timestamp': True,
                'output': True,
            }},
            {'$sort': {
                'timestamp': pymongo.ASCENDING,
            }},
            {'$group': {
                '_id': None,
                'output': {'$push': '$output'},
            }},
        ])['result']

        if output:
            output = output[0]['output']

        return '\n'.join(output)

    def initialize(self):
        self.generate_dh_param()

    def queue_dh_params(self, block=False):
        queue.start('dh_params', block=block, server_id=self.id,
            dh_param_bits=self.dh_param_bits, priority=HIGH)
        self.dh_params = None

        if block:
            self.load()

    def get_cache_key(self, suffix=None):
        if not self.cache_prefix:
            raise AttributeError('Cached config object requires cache_prefix')
        key = self.cache_prefix + '-' + self.id
        if suffix:
            key += '-%s' % suffix
        return key

    def get_ip_set(self, org_id, user_id):
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

    def _event_delay(self, type, resource_id=None):
        # Min event every 1s max event every 0.2s
        event_time = time.time()
        if event_time - self._last_event >= 1:
            self._last_event = event_time
            self._cur_event = uuid.uuid4()
            event.Event(type=type, resource_id=resource_id)
            return

        def _target():
            event_id = uuid.uuid4()
            self._cur_event = event_id
            time.sleep(0.2)
            if self._cur_event == event_id:
                self._last_event = time.time()
                event.Event(type=type, resource_id=resource_id)
        threading.Thread(target=_target).start()

    def commit(self, *args, **kwargs):
        tran = None

        if self.network != self._orig_network:
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
                    old_network=self._orig_network,
                )
                self.network_lock = queue_ip_pool.id
        elif self._orgs_changed:
            # TODO update ip pool
            pass

        mongo.MongoObject.commit(self, transaction=tran,
            *args, **kwargs)

        if tran:
            messenger.publish('queue', 'queue_updated',
                transaction=tran)
            tran.commit()

    def remove(self):
        self._remove_primary_user()
        mongo.MongoObject.remove(self)

    def _create_primary_user(self):
        logger.debug('Creating primary user. %r' % {
            'server_id': self.id,
        })

        try:
            org = self.iter_orgs().next()
        except StopIteration:
            raise ServerMissingOrg('Primary user cannot be created ' + \
                'without any organizations', {
                    'server_id': self.id,
                })

        user = org.new_user(name=SERVER_USER_PREFIX + self.id,
            type=CERT_SERVER)

        self.primary_organization = org.id
        self.primary_user = user.id
        self.commit(('primary_organization', 'primary_user'))

        user.commit()

    def _remove_primary_user(self):
        logger.debug('Removing primary user. %r' % {
            'server_id': self.id,
        })

        if not self.primary_organization or not self.primary_user:
            return

        org = organization.get_org(id=self.primary_organization)
        if org:
            user = org.get_user(id=self.primary_user)
            if user:
                user.remove()

        self.primary_organization = None
        self.primary_user = None

    def add_org(self, org_id):
        if not isinstance(org_id, basestring):
            org_id = org_id.id
        logger.debug('Adding organization to server. %r' % {
            'server_id': self.id,
            'org_id': org_id,
        })
        if org_id in self.organizations:
            logger.debug('Organization already on server, skipping. %r' % {
                'server_id': self.id,
                'org_id': org_id,
            })
            return
        self.organizations.append(org_id)
        self.changed.add('organizations')
        self.generate_ca_cert()
        self._orgs_changed = True

    def remove_org(self, org_id):
        if not isinstance(org_id, basestring):
            org_id = org_id.id
        if org_id not in self.organizations:
            return
        logger.debug('Removing organization from server. %r' % {
            'server_id': self.id,
            'org_id': org_id,
        })
        if self.primary_organization == org_id:
            self._remove_primary_user()
        try:
            self.organizations.remove(org_id)
        except ValueError:
            pass
        self.changed.add('organizations')
        self.generate_ca_cert()
        self._orgs_changed = True

    def iter_orgs(self):
        for org_id in self.organizations:
            org = organization.get_org(id=org_id)
            if org:
                yield org
            else:
                logger.error('Removing non-existent organization ' +
                    'from server. %r' % {
                        'server_id': self.id,
                        'org_id': org_id,
                    })
                self.remove_org(org_id)
                self.commit('organizations')
                event.Event(type=SERVER_ORGS_UPDATED, resource_id=self.id)

    def get_org(self, org_id):
        if org_id in self.organizations:
            return organization.get_org(id=org_id)

    def add_host(self, host_id):
        if not isinstance(host_id, basestring):
            host_id = host_id.id
        logger.debug('Adding host to server. %r' % {
            'server_id': self.id,
            'host_id': host_id,
        })
        if host_id in self.hosts:
            logger.debug('Host already on server, skipping. %r' % {
                'server_id': self.id,
                'host_id': host_id,
            })
            return
        self.hosts.append(host_id)
        self.changed.add('hosts')

    def remove_host(self, host_id):
        if not isinstance(host_id, basestring):
            host_id = host_id.id
        if host_id not in self.hosts:
            return
        logger.debug('Removing host from server. %r' % {
            'server_id': self.id,
            'host_id': host_id,
        })
        try:
            self.hosts.remove(host_id)
        except ValueError:
            pass
        self.changed.add('hosts')

    def iter_hosts(self):
        for host_id in self.hosts:
            hst = host.get_host(id=host_id)
            if hst:
                yield hst
            else:
                logger.error('Removing non-existent host ' +
                    'from server. %r' % {
                        'server_id': self.id,
                        'host_id': host_id,
                    })
                self.remove_host(host_id)
                self.commit('hosts')
                event.Event(type=SERVER_HOSTS_UPDATED, resource_id=self.id)

    def get_host(self, host_id):
        if host_id in self.hosts:
            return host.get_host(id=host_id)

    def generate_dh_param(self):
        reserved = queue.reserve('pooled_dh_params', server=self)
        if not reserved:
            reserved = queue.reserve('queued_dh_params', server=self)

        if reserved:
            queue.start('dh_params', dh_param_bits=self.dh_param_bits,
                priority=LOW)
            return

        self.queue_dh_params()

    def _parse_network(self, network):
        network_split = network.split('/')
        address = network_split[0]
        cidr = int(network_split[1])
        subnet = ('255.' * (cidr / 8)) + str(
            int(('1' * (cidr % 8)).ljust(8, '0'), 2))
        subnet += '.0' * (3 - subnet.count('.'))
        return (address, subnet)

    def generate_ca_cert(self):
        ca_certificate = ''
        for org in self.iter_orgs():
            ca_certificate += org.ca_certificate
        self.ca_certificate = ca_certificate

    def _generate_ovpn_conf(self):
        logger.debug('Generating server ovpn conf. %r' % {
            'server_id': self.id,
        })

        if not self.primary_organization or not self.primary_user:
            self._create_primary_user()

        primary_org = organization.get_org(id=self.primary_organization)
        if not primary_org:
            self._create_primary_user()
            primary_org = organization.get_org(id=self.primary_organization)

        primary_user = primary_org.get_user(self.primary_user)
        if not primary_user:
            self._create_primary_user()
            primary_org = organization.get_org(id=self.primary_organization)
            primary_user = primary_org.get_user(self.primary_user)

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
                    self.id,
                ))

        push = ''
        if self.mode == LOCAL_TRAFFIC:
            for network in self.local_networks:
                push += 'push "route %s %s"\n' % self._parse_network(network)
        elif self.mode == VPN_TRAFFIC:
            pass
        else:
            push += 'push "redirect-gateway"\n'
        for dns_server in self.dns_servers:
            push += 'push "dhcp-option DNS %s"\n' % dns_server
        if self.search_domain:
            push += 'push "dhcp-option DOMAIN %s"\n' % self.search_domain

        server_conf = OVPN_INLINE_SERVER_CONF % (
            self.port,
            self.protocol,
            self.interface,
            tls_verify_path,
            client_connect_path,
            client_disconnect_path,
            '%s %s' % self._parse_network(self.network),
            ovpn_status_path,
            4 if self.debug else 1,
            8 if self.debug else 3,
        )

        if self.otp_auth:
            server_conf += 'auth-user-pass-verify %s via-file\n' % (
                user_pass_verify_path)

        if self.lzo_compression:
            server_conf += 'comp-lzo\npush "comp-lzo"\n'

        if self.mode in (LOCAL_TRAFFIC, VPN_TRAFFIC):
            server_conf += 'client-to-client\n'

        if push:
            server_conf += push

        server_conf += '<ca>\n%s\n</ca>\n' % utils.get_cert_block(
            self.ca_certificate)
        server_conf += '<cert>\n%s\n</cert>\n' % utils.get_cert_block(
            primary_user.certificate)
        server_conf += '<key>\n%s\n</key>\n' % primary_user.private_key
        server_conf += '<dh>\n%s\n</dh>\n' % self.dh_params

        with open(ovpn_conf_path, 'w') as ovpn_conf:
            os.chmod(ovpn_conf_path, 0600)
            ovpn_conf.write(server_conf)

    def _enable_ip_forwarding(self):
        try:
            subprocess.check_call(['sysctl', '-w', 'net.ipv4.ip_forward=1'],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError:
            logger.exception('Failed to enable IP forwarding. %r' % {
                'server_id': self.id,
            })
            raise

    def _generate_iptables_rules(self):
        rules = []

        try:
            routes_output = subprocess.check_output(['route', '-n'],
                stderr=subprocess.PIPE)
        except subprocess.CalledProcessError:
            logger.exception('Failed to get IP routes. %r' % {
                'server_id': self.id,
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
                'server_id': self.id,
            })
        default_interface = routes['0.0.0.0']

        rules.append(['INPUT', '-i', self.interface, '-j', 'ACCEPT'])
        rules.append(['FORWARD', '-i', self.interface, '-j', 'ACCEPT'])

        interfaces = set()
        for network_address in self.local_networks or ['0.0.0.0/0']:
            args = ['POSTROUTING', '-t', 'nat']
            network = self._parse_network(network_address)[0]

            if network not in routes:
                logger.debug('Failed to find interface for local network ' + \
                        'route, using default route. %r' % {
                    'server_id': self.id,
                })
                interface = default_interface
            else:
                interface = routes[network]
            interfaces.add(interface)

            if network != '0.0.0.0':
                args += ['-d', network_address]

            args += ['-s', self.network, '-o', interface, '-j', 'MASQUERADE']
            rules.append(args)

        for interface in interfaces:
            rules.append(['FORWARD', '-i', interface, '-o', self.interface,
                '-m', 'state', '--state', 'ESTABLISHED,RELATED',
                '-j', 'ACCEPT'])
            rules.append(['FORWARD', '-i', self.interface, '-o', interface,
                '-m', 'state', '--state', 'ESTABLISHED,RELATED',
                '-j', 'ACCEPT'])

        return rules

    def _exists_iptables_rules(self, rule):
        logger.debug('Checking for iptables rule. %r' % {
            'server_id': self.id,
            'rule': rule,
        })
        try:
            subprocess.check_call(['iptables', '-C'] + rule,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError:
            return False
        return True

    def _set_iptables_rules(self):
        logger.debug('Setting iptables rules. %r' % {
            'server_id': self.id,
        })
        for rule in self._generate_iptables_rules():
            if not self._exists_iptables_rules(rule):
                try:
                    subprocess.check_call(['iptables', '-A'] + rule,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                except subprocess.CalledProcessError:
                    logger.exception('Failed to apply iptables ' + \
                        'routing rule. %r' % {
                            'server_id': self.id,
                            'rule': rule,
                        })
                    raise

    def _clear_iptables_rules(self):
        logger.debug('Clearing iptables rules. %r' % {
            'server_id': self.id,
        })
        for rule in self._generate_iptables_rules():
            if self._exists_iptables_rules(rule):
                try:
                    subprocess.check_call(['iptables', '-D'] + rule,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                except subprocess.CalledProcessError:
                    logger.exception('Failed to clear iptables ' + \
                        'routing rule. %r' % {
                            'server_id': self.id,
                            'rule': rule,
                        })
                    raise

    def _sub_thread(self, cursor_id, process):
        for msg in self.subscribe(cursor_id=cursor_id):
            message = msg['message']

            try:
                if message == 'stop':
                    self._state = False
                    process.send_signal(signal.SIGINT)
                elif message == 'force_stop':
                    self._state = False
                    process.send_signal(signal.SIGKILL)
                elif message == 'stopped':
                    break
            except OSError:
                pass

    def _status_thread(self):
        i = 0
        cur_client_count = 0
        ovpn_status_path = os.path.join(self._temp_path, OVPN_STATUS_NAME)
        while not self._interrupt:
            time.sleep(0.1)
            # Check interrupt every 0.1s check client count every 5s
            if i >= settings.vpn.status_update_rate * 10:
                i = 0
                self._read_clients(ovpn_status_path)
            else:
                i += 1
        self._clear_iptables_rules()

    def _run_thread(self):
        logger.debug('Starting ovpn process. %r' % {
            'server_id': self.id,
        })
        cursor_id = self.get_cursor_id()

        self._interrupt = False
        self._state = True
        self._clients = {}

        try:
            ovpn_conf_path = os.path.join(self._temp_path, OVPN_CONF_NAME)
            try:
                process = subprocess.Popen(['openvpn', ovpn_conf_path],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except OSError:
                self.push_output(traceback.format_exc())
                logger.exception('Failed to start ovpn process. %r' % {
                    'server_id': self.id,
                })
                self.publish('stopped')
                return

            sub_thread = threading.Thread(target=self._sub_thread,
                args=(cursor_id, process))
            sub_thread.start()
            status_thread = threading.Thread(target=self._status_thread)
            status_thread.start()
            self.status = True
            self.start_timestamp = datetime.datetime.now()
            self.commit(('status', 'start_timestamp'))
            self.publish('started')

            while True:
                line = process.stdout.readline()
                if not line:
                    if process.poll() is not None:
                        break
                    else:
                        continue
                self.push_output(line)

            self._interrupt = True
            status_thread.join()

            self.status = False
            self.start_timestamp = None
            self.commit(('status', 'start_timestamp'))
            self.publish('stopped')
            self.update_clients({}, force=True)
            if self._state:
                event.Event(type=SERVERS_UPDATED)
                logger.LogEntry(message='Server stopped unexpectedly "%s".' % (
                    self.name))

            logger.debug('Ovpn process has ended. %r' % {
                'server_id': self.id,
            })
        except:
            messenger.publish('server_instance', 'stopped', {
                'server_id': self.id,
            })

    def get_cursor_id(self):
        return messenger.get_cursor_id('servers')

    def publish(self, message, transaction=None):
        messenger.publish('servers', message, extra={
            'server_id': self.id,
        }, transaction=transaction)

    def subscribe(self, cursor_id=None, timeout=None):
        for msg in messenger.subscribe('servers', cursor_id=cursor_id,
                timeout=timeout):
            if msg.get('server_id') == self.id:
                yield msg

    def start(self, timeout=VPN_OP_TIMEOUT):
        if self.status:
            return

        if not self.organizations:
            raise ServerMissingOrg('Server cannot be started ' + \
                'without any organizations', {
                    'server_id': self.id,
                })

        os.makedirs(self._temp_path)

        ovpn_conf_path = self._generate_ovpn_conf()
        self._enable_ip_forwarding()
        self._set_iptables_rules()
        self.clear_output()
        cursor_id = self.get_cursor_id()

        threading.Thread(target=self._run_thread).start()

        for msg in self.subscribe(cursor_id=cursor_id, timeout=timeout):
            message = msg['message']
            if message == 'started':
                self.status = True
                return
            elif message == 'stopped':
                raise ServerStartError('Server failed to start', {
                    'server_id': self.id,
                })

        raise ServerStartError('Server start timed out', {
                'server_id': self.id,
            })

    def stop(self, timeout=VPN_OP_TIMEOUT, force=False):
        # TODO may need locking
        if not self.status:
            return

        logger.debug('Stopping server. %r' % {
            'server_id': self.id,
        })
        cursor_id = self.get_cursor_id()

        if force:
            self.publish('force_stop')
        else:
            self.publish('stop')

        for msg in self.subscribe(cursor_id=cursor_id, timeout=timeout):
            message = msg['message']
            if message == 'stopped':
                self.status = False
                return

        raise ServerStopError('Server stop timed out', {
                'server_id': self.id,
            })

    def force_stop(self, timeout=VPN_OP_TIMEOUT):
        self.stop(timeout=timeout, force=True)

    def restart(self):
        if not self.status:
            self.start()
            return
        logger.debug('Restarting server. %r' % {
            'server_id': self.id,
        })
        self.stop()
        self.start()

    def clear_output(self):
        self.output_collection.remove({
            'server_id': self.id,
        })
        self._event_delay(type=SERVER_OUTPUT_UPDATED, resource_id=self.id)

    def push_output(self, output):
        self.output_collection.insert({
            'server_id': self.id,
            'timestamp': datetime.datetime.utcnow(),
            'output': output.rstrip('\n'),
        })

        doc_ids = self.output_collection.aggregate([
            {'$match': {
                'server_id': self.id,
            }},
            {'$project': {
                '_id': True,
                'timestamp': True,
            }},
            {'$sort': {
                'timestamp': pymongo.DESCENDING,
            }},
            {'$skip': 10000},
            {'$group': {
                '_id': None,
                'doc_ids': {'$push': '$_id'},
            }},
        ])['result']

        if doc_ids:
            doc_ids = doc_ids[0]['doc_ids']

            self.output_collection.remove({
                '_id': {'$in': doc_ids},
            })

        self._event_delay(type=SERVER_OUTPUT_UPDATED, resource_id=self.id)

    def _update_clients_bandwidth(self, clients):
        # Remove client no longer connected
        for client_id in self._clients.iterkeys():
            if client_id not in clients:
                del self._clients[client_id]

        # Get total bytes send and recv for all clients
        bytes_recv_t = 0
        bytes_sent_t = 0
        for client_id in clients:
            bytes_recv = clients[client_id]['bytes_received']
            bytes_sent = clients[client_id]['bytes_sent']
            prev_bytes_recv, prev_bytes_sent = self._clients.get(
                client_id, (0, 0))
            self._clients[client_id] = (bytes_recv, bytes_sent)

            if prev_bytes_recv > bytes_recv or prev_bytes_sent > bytes_sent:
                prev_bytes_recv = 0
                prev_bytes_sent = 0

            bytes_recv_t += bytes_recv - prev_bytes_recv
            bytes_sent_t += bytes_sent - prev_bytes_sent

        if bytes_recv_t != 0 or bytes_sent_t != 0:
            self.bandwidth.add_data(
                datetime.datetime.utcnow(), bytes_recv_t, bytes_sent_t)

    def _read_clients(self, ovpn_status_path):
        clients = {}
        if os.path.isfile(ovpn_status_path):
            with open(ovpn_status_path, 'r') as status_file:
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

    def update_clients(self, clients, force=False):
        if not force and not self.status:
            return
        # Openvpn will create an undef client while a client connects
        clients.pop('UNDEF', None)
        self._update_clients_bandwidth(clients)
        client_count = len(self.clients)
        self.clients = clients
        self.commit('clients')
        if force or client_count != len(clients):
            for org_id in self.organizations:
                event.Event(type=USERS_UPDATED, resource_id=org_id)
            if not force:
                event.Event(type=SERVERS_UPDATED)
