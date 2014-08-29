from constants import *
from exceptions import *
from descriptors import *
from pritunl import app_server
from organization import Organization
from event import Event
from log_entry import LogEntry
from server_bandwidth import ServerBandwidth
from server_ip_pool import ServerIpPool
from mongo_object import MongoObject
from cache import cache_db
import mongo
import uuid
import os
import signal
import time
import datetime
import subprocess
import threading
import logging
import traceback
import utils
import re
import json
import ipaddress

logger = logging.getLogger(APP_NAME)

class Server(MongoObject):
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
        'primary_organization',
        'primary_user',
        'ca_certificate',
        'dh_params',

        'instance_id',
        'ping_timestamp',
        'status',
        'uptime',
        'clients',
        'users_online',
    }
    fields_default = {
        'network_lock': False,
        'dns_servers': [],
        'otp_auth': False,
        'lzo_compression': False,
        'debug': False,
        'organizations': [],
        'status': False,
        'clients': {},
        'users_online': 0,
    }
    cache_prefix = 'server'

    def __init__(self, name=None, network=None, interface=None, port=None,
            protocol=None, dh_param_bits=None, mode=None, local_networks=None,
            dns_servers=None, search_domain=None, public_address=None,
            otp_auth=None, lzo_compression=None, debug=None, **kwargs):
        MongoObject.__init__(self, **kwargs)

        self._cur_event = None
        self._last_event = 0
        self._orig_network = self.network
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

    @static_property
    def collection(cls):
        return mongo.get_collection('servers')

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

    @cached_property
    def user_count(self):
        return Organization.get_user_count_multi(org_ids=self.organizations)

    @cached_property
    def output(self):
        return '\n'.join(cache_db.list_elements(self.get_cache_key('output')))

    def initialize(self):
        self.generate_dh_param()

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
            # TODO
            pass

    def unassign_ip_addr(self, org_id, user_id):
        if not self.network_lock:
            self.ip_pool.unassign_ip_addr(org_id, user_id)
        else:
            # TODO
            pass

    def _event_delay(self, type, resource_id=None):
        # Min event every 1s max event every 0.2s
        event_time = time.time()
        if event_time - self._last_event >= 1:
            self._last_event = event_time
            self._cur_event = uuid.uuid4()
            Event(type=type, resource_id=resource_id)
            return

        def _target():
            event_id = uuid.uuid4()
            self._cur_event = event_id
            time.sleep(0.2)
            if self._cur_event == event_id:
                self._last_event = time.time()
                Event(type=type, resource_id=resource_id)
        threading.Thread(target=_target).start()

    def commit(self, *args, **kwargs):
        if self.network != self._orig_network and self.network_lock:
            raise ServerNetworkLocked('Server network is locked')
        MongoObject.commit(self, *args, **kwargs)
        if self.network != self._orig_network:
            # TODO
            self.ip_pool.assign_ip_pool(self._orig_network)

    def remove(self):
        self._remove_primary_user()
        MongoObject.remove(self)

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

        org = Organization.get_org(id=self.primary_organization)
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
        self.generate_ca_cert()

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
        self.generate_ca_cert()

    def iter_orgs(self):
        for org_id in self.organizations:
            org = Organization.get_org(id=org_id)
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

    def get_org(self, org_id):
        if org_id in self.organizations:
            return Organization.get_org(id=org_id)

    def generate_dh_param(self):
        logger.debug('Generating server dh params. %r' % {
            'server_id': self.id,
        })

        temp_path = app_server.get_temp_path()
        dh_param_path = os.path.join(temp_path, DH_PARAM_NAME)

        try:
            os.makedirs(temp_path)
            args = [
                'openssl', 'dhparam',
                '-out', dh_param_path,
                str(self.dh_param_bits),
            ]
            subprocess.check_call(args, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
            self.read_file('dh_params', dh_param_path)
        finally:
            utils.rmtree(temp_path)

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

    def _generate_ovpn_conf(self, temp_path):
        logger.debug('Generating server ovpn conf. %r' % {
            'server_id': self.id,
        })

        if not self.primary_organization or not self.primary_user:
            self._create_primary_user()

        primary_org = Organization.get_org(id=self.primary_organization)
        if not primary_org:
            self._create_primary_user()
            primary_org = Organization.get_org(id=self.primary_organization)

        primary_user = primary_org.get_user(self.primary_user)
        if not primary_user:
            self._create_primary_user()
            primary_org = Organization.get_org(id=self.primary_organization)
            primary_user = primary_org.get_user(self.primary_user)

        tls_verify_path = os.path.join(temp_path,
            TLS_VERIFY_NAME)
        user_pass_verify_path = os.path.join(temp_path,
            USER_PASS_VERIFY_NAME)
        client_connect_path = os.path.join(temp_path,
            CLIENT_CONNECT_NAME)
        client_disconnect_path = os.path.join(temp_path,
            CLIENT_DISCONNECT_NAME)
        ovpn_status_path = os.path.join(temp_path,
            OVPN_STATUS_NAME)
        ovpn_conf_path = os.path.join(temp_path,
            OVPN_CONF_NAME)

        auth_host = app_server.bind_addr
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
                    app_server.server_api_key,
                    '/dev/null', # TODO
                    app_server.web_protocol,
                    auth_host,
                    app_server.port,
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

    def _sub_thread(self, process):
        for message in cache_db.subscribe(self.get_cache_key()):
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

    def _status_thread(self, temp_path):
        i = 0
        cur_client_count = 0
        ovpn_status_path = os.path.join(temp_path, OVPN_STATUS_NAME)
        while not self._interrupt:
            time.sleep(0.1)
            # Check interrupt every 0.1s check client count every 5s
            if i == SERVER_STATUS_RATE * 5:
                i = 0
                self._read_clients(ovpn_status_path)
            else:
                i += 1
        self._clear_iptables_rules()

    def _run_thread(self, temp_path):
        logger.debug('Starting ovpn process. %r' % {
            'server_id': self.id,
        })
        self._interrupt = False
        self._state = True
        try:
            ovpn_conf_path = os.path.join(temp_path, OVPN_CONF_NAME)
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
            cache_db.dict_set(self.get_cache_key(), 'start_time',
                str(int(time.time() - 1)))
            sub_thread = threading.Thread(target=self._sub_thread,
                args=(process,))
            sub_thread.start()
            status_thread = threading.Thread(target=self._status_thread,
                args=(temp_path,))
            status_thread.start()
            self.status = True
            self.commit('status')
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

            cache_db.remove(self.get_cache_key('clients'))
            cache_db.dict_remove(self.get_cache_key(), 'clients')

            self.status = False
            self.commit('status')
            self.publish('stopped')
            self.update_clients({}, force=True)
            if self._state:
                Event(type=SERVERS_UPDATED)
                LogEntry(message='Server stopped unexpectedly "%s".' % (
                    self.name))

            logger.debug('Ovpn process has ended. %r' % {
                'server_id': self.id,
            })
        except:
            self._interrupt = True
            self.publish('stopped')
            raise

    def publish(self, message):
        cache_db.publish(self.get_cache_key(), message)

    def start(self):
        temp_path = app_server.get_temp_path()

        if not self.organizations:
            raise ServerMissingOrg('Server cannot be started ' + \
                'without any organizations', {
                    'server_id': self.id,
                })

        os.makedirs(temp_path)

        ovpn_conf_path = self._generate_ovpn_conf(temp_path)
        self._enable_ip_forwarding()
        self._set_iptables_rules()
        self.clear_output()

        threading.Thread(target=self._run_thread,
            args=(temp_path,)).start()

        started = False
        for message in cache_db.subscribe(self.get_cache_key(),
                SUB_RESPONSE_TIMEOUT):
            if message == 'started':
                started = True
                break
            elif message == 'stopped':
                raise ServerStartError('Server failed to start', {
                    'server_id': self.id,
                })
        if not started:
            raise ServerStartError('Server thread failed to return ' + \
                'start event', {
                    'server_id': self.id,
                })

    def stop(self):
        cache_db.lock_acquire(self.get_cache_key('op_lock'))
        try:
            if not self.status:
                return
            logger.debug('Stopping server. %r' % {
                'server_id': self.id,
            })

            stopped = False
            self.publish('stop')
            for message in cache_db.subscribe(self.get_cache_key(),
                    SUB_RESPONSE_TIMEOUT):
                if message == 'stopped':
                    stopped = True
                    break
            if not stopped:
                raise ServerStopError('Server thread failed to return ' + \
                    'stop event', {
                        'server_id': self.id,
                    })
        finally:
            cache_db.lock_release(self.get_cache_key('op_lock'))

    def force_stop(self):
        cache_db.lock_acquire(self.get_cache_key('op_lock'))
        try:
            if not self.status:
                return
            logger.debug('Forcing stop server. %r' % {
                'server_id': self.id,
            })

            stopped = False
            self.publish('force_stop')
            for message in cache_db.subscribe(self.get_cache_key(),
                    SUB_RESPONSE_TIMEOUT):
                if message == 'stopped':
                    stopped = True
                    break
            if not stopped:
                raise ServerStopError('Server thread failed to return ' + \
                    'stop event', {
                        'server_id': self.id,
                    })
        finally:
            cache_db.lock_release(self.get_cache_key('op_lock'))

    def restart(self):
        if not self.status:
            self.start()
            return
        logger.debug('Restarting server. %r' % {
            'server_id': self.id,
        })
        self.stop()
        self.start()

    def get_output(self):
        return self.output

    def clear_output(self):
        cache_db.remove(self.get_cache_key('output'))
        self._event_delay(type=SERVER_OUTPUT_UPDATED, resource_id=self.id)

    def push_output(self, output):
        if not SERVER_LOG_LINES:
            return
        cache_db.list_rpush(self.get_cache_key('output'), output.rstrip('\n'))
        clear_lines = cache_db.list_length(self.get_cache_key('output')) - \
            SERVER_LOG_LINES
        for _ in xrange(clear_lines):
            cache_db.list_lpop(self.get_cache_key('output'))
        self._event_delay(type=SERVER_OUTPUT_UPDATED, resource_id=self.id)

    def get_bandwidth(self, period):
        server_bandwidth = ServerBandwidth(self.id)
        return server_bandwidth.get_bandwidth(period)

    def get_bandwidth_random(self, period=None):
        # Generate random bandwidth data for demo and write to file
        import json
        import random
        data = {}
        date = datetime.datetime.utcnow()
        date -= datetime.timedelta(microseconds=date.microsecond,
            seconds=date.second)
        periods = (period,) if period else ('1m', '5m', '30m', '2h', '1d')

        for period in periods:
            if period == '1m':
                date_end = date
                date_cur = date_end - datetime.timedelta(hours=6)
                date_step = datetime.timedelta(minutes=1)
                bytes_recv = 700000
                bytes_sent = 700000
                bandwidth_rand = lambda x: random.randint(
                    max(x - 50000, 0), max(x + 50000, 0))
            elif period == '5m':
                date_end = date - datetime.timedelta(minutes=date.minute % 5)
                date_cur = date_end - datetime.timedelta(days=1)
                date_step = datetime.timedelta(minutes=5)
                bytes_recv = 3500000
                bytes_sent = 3500000
                bandwidth_rand = lambda x: random.randint(
                    max(x - 250000, 0), max(x + 250000, 0))
            elif period == '30m':
                date_end = date - datetime.timedelta(minutes=date.minute % 30)
                date_cur = date_end - datetime.timedelta(days=7)
                date_step = datetime.timedelta(minutes=30)
                bytes_recv = 21000000
                bytes_sent = 21000000
                bandwidth_rand = lambda x: random.randint(
                    max(x - 2000000, 0), max(x + 2000000, 0))
            elif period == '2h':
                date_end = date - datetime.timedelta(minutes=date.minute,
                    hours=date.hour % 2)
                date_cur = date_end - datetime.timedelta(days=30)
                date_step = datetime.timedelta(hours=2)
                bytes_recv = 84000000
                bytes_sent = 84000000
                bandwidth_rand = lambda x: random.randint(
                    max(x - 2000000, 0), max(x + 2000000, 0))
            elif period == '1d':
                date_end = date - datetime.timedelta(minutes=date.minute,
                    hours=date.hour)
                date_cur = date_end - datetime.timedelta(days=365)
                date_step = datetime.timedelta(days=1)
                bytes_recv = 1008000000
                bytes_sent = 1008000000
                bandwidth_rand = lambda x: random.randint(
                    max(x - 100000000, 0), max(x + 100000000, 0))

            data_p = {
                'received': [],
                'received_total': 0,
                'sent': [],
                'sent_total': 0,
            }
            data[period] = data_p

            while date_cur < date_end:
                date_cur += date_step

                timestamp = int(date_cur.strftime('%s'))
                bytes_recv = bandwidth_rand(bytes_recv)
                bytes_sent = bandwidth_rand(bytes_sent)

                data_p['received'].append((timestamp, bytes_recv))
                data_p['received_total'] += bytes_recv
                data_p['sent'].append((timestamp, bytes_sent))
                data_p['sent_total'] += bytes_sent

        if len(periods) == 1:
            path = os.path.join(app_server.data_path,
                'demo_bandwidth_%s' % periods[0])
            with open(path, 'w') as demo_file:
                demo_file.write(json.dumps(data[periods[0]]))
            return data[periods[0]]
        else:
            path = os.path.join(app_server.data_path, 'demo_bandwidth')
            with open(path, 'w') as demo_file:
                demo_file.write(json.dumps(data))
            return data

    def _update_clients_bandwidth(self, clients):
        # Remove client no longer connected
        for client_id in cache_db.dict_keys(self.get_cache_key('clients')):
            if client_id not in clients:
                cache_db.dict_remove(self.get_cache_key('clients'), client_id)

        # Get total bytes send and recv for all clients
        bytes_recv_t = 0
        bytes_sent_t = 0
        for client_id in clients:
            bytes_recv = clients[client_id]['bytes_received']
            bytes_sent = clients[client_id]['bytes_sent']
            prev_bytes_recv = 0
            prev_bytes_sent = 0
            client_prev = cache_db.dict_get(self.get_cache_key('clients'),
                client_id)
            cache_db.dict_set(self.get_cache_key('clients'), client_id,
                '%s,%s' % (bytes_recv, bytes_sent))

            if client_prev:
                client_prev = client_prev.split(',')
                prev_bytes_recv = int(client_prev[0])
                prev_bytes_sent = int(client_prev[1])

            if prev_bytes_recv > bytes_recv or prev_bytes_sent > bytes_sent:
                prev_bytes_recv = 0
                prev_bytes_sent = 0

            bytes_recv_t += bytes_recv - prev_bytes_recv
            bytes_sent_t += bytes_sent - prev_bytes_sent

        if bytes_recv_t != 0 or bytes_sent_t != 0:
            server_bandwidth = ServerBandwidth(self.id)
            server_bandwidth.add_bandwidth(
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
                Event(type=USERS_UPDATED, resource_id=org_id)
            if not force:
                Event(type=SERVERS_UPDATED)

    @classmethod
    def new_server(cls, **kwargs):
        server = cls(**kwargs)
        server.initialize()
        return server

    @classmethod
    def get_server(cls, id):
        return cls(id=id)

    @classmethod
    def iter_servers(cls):
        for doc in cls.collection.find().sort('name'):
            yield cls(doc=doc)
