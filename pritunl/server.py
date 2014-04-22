from constants import *
from exceptions import *
from pritunl import app_server
from config import Config
from organization import Organization
from event import Event
from log_entry import LogEntry
from cache import cache_db, persist_db
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

class Server(Config):
    str_options = {'name', 'network', 'interface', 'protocol', 'mode',
        'local_networks', 'public_address', 'primary_organization',
        'primary_user', 'organizations', 'local_network', 'dns_servers'}
    bool_options = {'otp_auth', 'lzo_compression', 'debug'}
    int_options = {'port', 'dh_param_bits'}
    list_options = {'organizations', 'local_networks', 'dns_servers'}
    cached = True
    cache_prefix = 'server'
    type = 'server'

    def __init__(self, id=None, **kwargs):
        Config.__init__(self)
        self._cur_event = None
        self._last_event = 0
        self._rebuild_dh_params = False
        self._reset_ip_pool = False

        if id is None:
            self.id = uuid.uuid4().hex
            for name, value in kwargs.iteritems():
                setattr(self, name, value)
        else:
            self.id = id

        self.path = os.path.join(app_server.data_path, SERVERS_DIR, self.id)
        self.ovpn_conf_path = os.path.join(self.path, TEMP_DIR, OVPN_CONF_NAME)
        self.dh_param_path = os.path.join(self.path, DH_PARAM_NAME)
        self.ip_pool_path = os.path.join(self.path, IP_POOL_NAME)
        self.ca_cert_path = os.path.join(self.path, TEMP_DIR, OVPN_CA_NAME)
        self.tls_verify_path = os.path.join(self.path, TEMP_DIR,
            TLS_VERIFY_NAME)
        self.user_pass_verify_path = os.path.join(self.path, TEMP_DIR,
            USER_PASS_VERIFY_NAME)
        self.client_connect_path = os.path.join(self.path, TEMP_DIR,
            CLIENT_CONNECT_NAME)
        self.client_disconnect_path = os.path.join(self.path, TEMP_DIR,
            CLIENT_DISCONNECT_NAME)
        self.ovpn_status_path = os.path.join(self.path, TEMP_DIR,
            OVPN_STATUS_NAME)
        self.auth_log_path = os.path.join(app_server.data_path, AUTH_LOG_NAME)
        self.set_path(os.path.join(self.path, SERVER_CONF_NAME))

        if id is None:
            self._initialize()

    def __setattr__(self, name, value):
        if name == 'status':
            cache_db.dict_set(self.get_cache_key(), name,
                't' if value else 'f')
            return
        elif name == 'clients':
            cache_db.dict_set(self.get_cache_key(), name, json.dumps(value))
            return
        elif name == 'dh_param_bits':
            if not self._loaded or self.dh_param_bits != value:
                self._rebuild_dh_params = True
        elif name == 'network':
            self._reset_ip_pool = self._loaded and self.network != value
        Config.__setattr__(self, name, value)

    def __getattr__(self, name):
        if name == 'status':
            return cache_db.dict_get(self.get_cache_key(), name) == 't'
        elif name == 'uptime':
            if self.status:
                return int(time.time()) - int(cache_db.dict_get(
                    self.get_cache_key(), 'start_time'))
            return None
        elif name == 'clients':
            clients = cache_db.dict_get(self.get_cache_key(), name)
            if self.status and clients:
                return json.loads(clients)
            return {}
        elif name == 'output':
            return '\n'.join(cache_db.list_elements(
                self.get_cache_key('output')))
        elif name == 'user_count':
            return self._get_user_count()
        elif name == 'org_count':
            return self._get_org_count()
        return Config.__getattr__(self, name)

    def dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
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
            'public_address': self.public_address,
            'otp_auth': True if self.otp_auth else False,
            'lzo_compression': self.lzo_compression,
            'debug': True if self.debug else False,
            'org_count': self.org_count,
        }

    def load(self, *args, **kwargs):
        Config.load(self, *args, **kwargs)
        self._load_ip_pool()

    def _upgrade_0_10_5(self):
        if self.local_network:
            logger.debug('Upgrading server to v0.10.5... %r' % {
                'server_id': self.id,
            })
            self.local_networks = [self.local_network]
            self.local_network = None
            self.commit()

    def _upgrade_0_10_6(self):
        if not self.dh_param_bits:
            logger.debug('Upgrading server to v0.10.6... %r' % {
                'server_id': self.id,
            })
            self.dh_param_bits = app_server.dh_param_bits
            self.commit()

    def _upgrade_0_10_9(self):
        if not self.mode:
            logger.debug('Upgrading server to v0.10.9... %r' % {
                'server_id': self.id,
            })
            if self.local_networks:
                self.mode = LOCAL_TRAFFIC
            else:
                self.mode = VPN_TRAFFIC
            self.commit()

        self.update_ip_pool()

        try:
            ifc_pool_path = os.path.join(self.path, 'ifc_pool')
            if os.path.exists(ifc_pool_path):
                os.remove(ifc_pool_path)
        except:
            pass

    def _initialize(self):
        logger.debug('Initialize new server. %r' % {
            'server_id': self.id,
        })
        os.makedirs(os.path.join(self.path, TEMP_DIR))
        try:
            self._generate_dh_param()
            cache_db.set_add('servers', '%s_%s' % (self.id, self.type))
            self.commit()
            LogEntry(message='Created new server "%s".' % self.name)
        except:
            logger.exception('Failed to create server. %r' % {
                'server_id': self.id,
            })
            self.clear_cache()
            utils.rmtree(self.path)
            raise

    def _load_ip_pool(self):
        if cache_db.get(self.get_cache_key('ip_pool_cached')) == 't':
            return
        reset = False

        if os.path.exists(self.ip_pool_path):
            with open(self.ip_pool_path, 'r') as ip_pool_file:
                pool = json.loads(ip_pool_file.read())

            network = pool.pop('network', None)
            if network == self.network:
                cache_key = self.get_cache_key('ip_pool')
                set_cache_key = self.get_cache_key('ip_pool_set')
                for key, value in pool.iteritems():
                    cache_db.dict_set(cache_key, key, value)
                    local_ip_addr, remote_ip_addr = value.split('-')
                    cache_db.set_add(set_cache_key, local_ip_addr)
                    cache_db.set_add(set_cache_key, remote_ip_addr)
            else:
                reset = True

        cache_db.set(self.get_cache_key('ip_pool_cached'), 't')

        if reset:
            self.update_ip_pool()

    def _commit_ip_pool(self):
        with open(self.ip_pool_path, 'w') as ip_pool_file:
            pool = cache_db.dict_get_all(self.get_cache_key('ip_pool'))
            pool['network'] = self.network
            ip_pool_file.write(json.dumps(pool))

    def update_ip_pool(self):
        cache_key = self.get_cache_key('ip_pool')
        set_cache_key = self.get_cache_key('ip_pool_set')
        cache_db.lock_acquire(cache_key)
        try:
            ip_pool = ipaddress.IPv4Network(self.network).iterhosts()
            ip_pool.next()

            users = set()
            for org in self.iter_orgs():
                for user in org.iter_users():
                    if user.type == CERT_CLIENT:
                        users.add(org.id + '-' + user.id)

            for user_id in cache_db.dict_keys(cache_key) - users:
                ip_set = cache_db.dict_get(cache_key, user_id)
                local_ip_addr, remote_ip_addr = ip_set.split('-')
                cache_db.set_remove(set_cache_key, local_ip_addr)
                cache_db.set_remove(set_cache_key, remote_ip_addr)
                cache_db.dict_remove(cache_key, user_id)

            try:
                for user_id in users - cache_db.dict_keys(cache_key):
                    while True:
                        remote_ip_addr = str(ip_pool.next())
                        ip_addr_endpoint = remote_ip_addr.split('.')[-1]
                        if ip_addr_endpoint not in VALID_IP_ENDPOINTS:
                            continue
                        local_ip_addr = str(ip_pool.next())

                        if not cache_db.set_exists(set_cache_key,
                                local_ip_addr) and not cache_db.set_exists(
                                set_cache_key, remote_ip_addr):
                            cache_db.set_add(set_cache_key, local_ip_addr)
                            cache_db.set_add(set_cache_key, remote_ip_addr)
                            break
                    cache_db.dict_set(cache_key, user_id,
                        local_ip_addr + '-' + remote_ip_addr)
            except StopIteration:
                pass
            finally:
                self._commit_ip_pool()
                for org in self.iter_orgs():
                    Event(type=USERS_UPDATED, resource_id=org.id)
        finally:
            cache_db.lock_release(cache_key)

    def get_ip_set(self, org_id, user_id):
        ip_set = cache_db.dict_get(self.get_cache_key('ip_pool'),
            org_id + '-' + user_id)
        if ip_set:
            return ip_set.split('-')
        return None, None

    def _clear_list_cache(self):
        cache_db.set_remove('servers', '%s_%s' % (self.id, self.type))
        cache_db.list_remove('servers_sorted', '%s_%s' % (self.id, self.type))

    def clear_cache(self):
        self._clear_list_cache()
        cache_db.remove(self.get_cache_key('clients'))
        cache_db.remove(self.get_cache_key('ip_pool'))
        cache_db.remove(self.get_cache_key('ip_pool_set'))
        cache_db.remove(self.get_cache_key('ip_pool_cached'))
        for period in ('1m', '5m', '30m', '2h', '1d'):
            persist_db.remove(self.get_cache_key('bandwidth-%s' % period))
        Config.clear_cache(self)

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

    def remove(self):
        logger.debug('Removing server. %r' % {
            'server_id': self.id,
        })
        self._clear_list_cache()
        name = self.name
        orgs = list(self.iter_orgs())

        if self.status:
            self.force_stop(True)
        self.clear_cache()

        self._remove_primary_user()
        utils.rmtree(self.path)
        LogEntry(message='Deleted server "%s".' % name)
        Event(type=SERVERS_UPDATED)
        for org in orgs:
            Event(type=USERS_UPDATED, resource_id=org.id)

    def commit(self):
        if self._rebuild_dh_params:
            self._generate_dh_param()
        if self._reset_ip_pool:
            cache_db.remove(self.get_cache_key('ip_pool'))
            cache_db.remove(self.get_cache_key('ip_pool_set'))
            self.update_ip_pool()
        Config.commit(self)
        self.sort_servers_cache()
        Event(type=SERVERS_UPDATED)

    def _create_primary_user(self):
        if not self.org_count:
            raise ServerMissingOrg('Primary user cannot be created ' + \
                'without any organizations', {
                    'server_id': self.id,
                })
        logger.debug('Creating primary user. %r' % {
            'server_id': self.id,
        })
        org = self.iter_orgs().next()
        self.primary_organization = org.id
        user = org.new_user(CERT_SERVER, SERVER_USER_PREFIX + self.id)
        self.primary_user = user.id
        try:
            self.commit()
        except:
            logger.exception('Failed to commit server conf ' + \
                'on primary user creation, removing user. %r' % {
                    'server_id': self.id,
                    'user_id': user.id,
                })
            user.remove()
            raise

    def add_org(self, org_id):
        logger.debug('Adding organization to server. %r' % {
            'server_id': self.id,
            'org_id': org_id,
        })
        org = Organization.get_org(id=org_id)
        if org.id in self.organizations:
            logger.debug('Organization already on server, skipping. %r' % {
                'server_id': self.id,
                'org_id': org.id,
            })
            return org
        self.organizations.append(org.id)
        self.commit()
        self.update_ip_pool()
        Event(type=SERVERS_UPDATED)
        Event(type=SERVER_ORGS_UPDATED, resource_id=self.id)
        Event(type=USERS_UPDATED, resource_id=org_id)
        return org

    def _remove_primary_user(self):
        logger.debug('Removing primary user. %r' % {
            'server_id': self.id,
        })
        primary_organization = self.primary_organization
        primary_user = self.primary_user
        self.primary_organization = None
        self.primary_user = None

        if not primary_organization or not primary_user:
            return

        org = Organization.get_org(id=primary_organization)
        user = org.get_user(primary_user)
        if not user:
            logger.debug('Primary user not found, skipping remove. %r' % {
                'server_id': self.id,
                'org_id': org.id,
            })
            return

        if user:
            user.remove()

    def remove_org(self, org_id):
        if org_id not in self.organizations:
            return
        logger.debug('Removing organization from server. %r' % {
            'server_id': self.id,
            'org_id': org_id,
        })
        if self.primary_organization == org_id:
            self._remove_primary_user()
        self.organizations.remove(org_id)
        self.commit()
        self.update_ip_pool()
        Event(type=SERVERS_UPDATED)
        Event(type=SERVER_ORGS_UPDATED, resource_id=self.id)
        Event(type=USERS_UPDATED, resource_id=org_id)

    def iter_orgs(self):
        orgs_dict = {}
        orgs_sort = []

        for org_id in self.organizations:
            org = Organization.get_org(id=org_id)
            if not org:
                continue
            name_id = '%s_%s' % (org.name, org.id)
            orgs_dict[name_id] = org
            orgs_sort.append(name_id)

        for name_id in sorted(orgs_sort):
            yield orgs_dict[name_id]

    def get_org(self, org_id):
        if org_id in self.organizations:
            org = Organization.get_org(id=org_id)
            try:
                org.load()
            except IOError:
                logger.exception('Failed to load org conf. %r' % {
                        'org_id': org_id,
                    })
                return
            return org

    def _get_user_count(self):
        users_count = 0
        for org in self.iter_orgs():
            users_count += org.user_count
        return users_count

    def _get_org_count(self):
        org_count = 0
        for org in self.iter_orgs():
            org_count += 1
        return org_count

    def _generate_dh_param(self):
        logger.debug('Generating server dh params. %r' % {
            'server_id': self.id,
        })
        self._rebuild_dh_params = False
        args = [
            'openssl', 'dhparam',
            '-out', self.dh_param_path,
            str(self.dh_param_bits)
        ]
        subprocess.check_call(args, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)

    def _parse_network(self, network):
        network_split = network.split('/')
        address = network_split[0]
        cidr = int(network_split[1])
        subnet = ('255.' * (cidr / 8)) + str(
            int(('1' * (cidr % 8)).ljust(8, '0'), 2))
        subnet += '.0' * (3 - subnet.count('.'))
        return (address, subnet)

    def generate_ca_cert(self):
        logger.debug('Generating server ca cert. %r' % {
            'server_id': self.id,
        })
        with open(self.ca_cert_path, 'w') as server_ca_cert:
            for org in self.iter_orgs():
                ca_path = org.ca_cert.cert_path
                with open(ca_path, 'r') as org_ca_cert:
                    server_ca_cert.write(org_ca_cert.read())

    def _generate_scripts(self):
        logger.debug('Generating openvpn scripts. %r' % {
            'server_id': self.id,
        })
        for script, script_path in (
                    (TLS_VERIFY_SCRIPT, self.tls_verify_path),
                    (USER_PASS_VERIFY_SCRIPT, self.user_pass_verify_path),
                    (CLIENT_CONNECT_SCRIPT, self.client_connect_path),
                    (CLIENT_DISCONNECT_SCRIPT, self.client_disconnect_path),
                ):
            with open(script_path, 'w') as script_file:
                os.chmod(script_path, 0755)
                script_file.write(script % (
                    self.auth_log_path,
                    app_server.web_protocol,
                    app_server.port,
                    self.id,
                ))

    def _generate_ovpn_conf(self, inline=False):
        if not self.org_count:
            raise ServerMissingOrg('Ovpn conf cannot be generated without ' + \
                'any organizations', {
                    'server_id': self.id,
                })

        logger.debug('Generating server ovpn conf. %r' % {
            'server_id': self.id,
        })

        if not self.primary_organization or not self.primary_user:
            self._create_primary_user()

        if not os.path.isfile(self.dh_param_path):
            self._generate_dh_param()

        primary_org = Organization.get_org(id=self.primary_organization)
        if not primary_org:
            self._create_primary_user()
        primary_org = Organization.get_org(id=self.primary_organization)

        primary_user = primary_org.get_user(self.primary_user)
        if not primary_user:
            self._create_primary_user()
        primary_user = primary_org.get_user(self.primary_user)

        self.generate_ca_cert()
        self._generate_scripts()

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
        push = push.rstrip()

        if not inline:
            server_conf = OVPN_SERVER_CONF % (
                self.port,
                self.protocol,
                self.interface,
                self.ca_cert_path,
                primary_user.cert_path,
                primary_user.key_path,
                self.tls_verify_path,
                self.client_connect_path,
                self.client_disconnect_path,
                self.dh_param_path,
                '%s %s' % self._parse_network(self.network),
                push,
                '120' if self.otp_auth else '60',
                self.ovpn_status_path,
                4 if self.debug else 1,
                8 if self.debug else 3,
            )
        else:
            server_conf = OVPN_INLINE_SERVER_CONF % (
                self.port,
                self.protocol,
                self.interface,
                self.tls_verify_path,
                self.client_connect_path,
                self.client_disconnect_path,
                '%s %s' % self._parse_network(self.network),
                push,
                '120' if self.otp_auth else '60',
                self.ovpn_status_path,
                4 if self.debug else 1,
                8 if self.debug else 3,
            )

        if self.otp_auth:
            server_conf += 'auth-user-pass-verify %s via-file\n' % (
                self.user_pass_verify_path)

        if self.lzo_compression:
            server_conf += 'comp-lzo\npush "comp-lzo"\n'

        if self.mode in (LOCAL_TRAFFIC, VPN_TRAFFIC):
            server_conf += 'client-to-client\n'

        if inline:
            server_conf += '<ca>\n%s\n</ca>\n' % utils.get_cert_block(
                self.ca_cert_path)
            server_conf += '<cert>\n%s\n</cert>\n' % utils.get_cert_block(
                primary_user.cert_path)
            server_conf += '<key>\n%s\n</key>\n' % open(
                primary_user.key_path).read().strip()
            server_conf += '<dh>\n%s\n</dh>\n' % open(
                self.dh_param_path).read().strip()

        with open(self.ovpn_conf_path, 'w') as ovpn_conf:
            if inline:
                os.chmod(self.ovpn_conf_path, 0600)
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

    def _status_thread(self):
        i = 0
        cur_client_count = 0
        while not self._interrupt:
            time.sleep(0.1)
            # Check interrupt every 0.1s check client count every 5s
            if i == SERVER_STATUS_RATE * 5:
                i = 0
                self._read_clients()
            else:
                i += 1
        self._clear_iptables_rules()

    def _run_thread(self):
        logger.debug('Starting ovpn process. %r' % {
            'server_id': self.id,
        })
        self._interrupt = False
        self._state = True
        try:
            try:
                process = subprocess.Popen(['openvpn', self.ovpn_conf_path],
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
            status_thread = threading.Thread(target=self._status_thread)
            status_thread.start()
            self.status = True
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

    def start(self, silent=False):
        cache_db.lock_acquire(self.get_cache_key('op_lock'))
        try:
            if self.status:
                return
            if not self.org_count:
                raise ServerMissingOrg('Server cannot be started without ' + \
                    'any organizations', {
                        'server_id': self.id,
                    })
            logger.debug('Starting server. %r' % {
                'server_id': self.id,
            })
            self._generate_ovpn_conf()
            self._enable_ip_forwarding()
            self._set_iptables_rules()
            self.clear_output()

            threading.Thread(target=self._run_thread).start()

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

            if not silent:
                Event(type=SERVERS_UPDATED)
                LogEntry(message='Started server "%s".' % self.name)
        finally:
            cache_db.lock_release(self.get_cache_key('op_lock'))

    def stop(self, silent=False):
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

            if not silent:
                Event(type=SERVERS_UPDATED)
                LogEntry(message='Stopped server "%s".' % self.name)
        finally:
            cache_db.lock_release(self.get_cache_key('op_lock'))

    def force_stop(self, silent=False):
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

            if not silent:
                Event(type=SERVERS_UPDATED)
                LogEntry(message='Stopped server "%s".' % self.name)
        finally:
            cache_db.lock_release(self.get_cache_key('op_lock'))

    def restart(self, silent=False):
        if not self.status:
            self.start()
            return
        logger.debug('Restarting server. %r' % {
            'server_id': self.id,
        })
        self.stop(True)
        self.start(True)
        if not silent:
            Event(type=SERVERS_UPDATED)
            LogEntry(message='Restarted server "%s".' % self.name)

    def get_output(self):
        return self.output

    def clear_output(self):
        cache_db.remove(self.get_cache_key('output'))
        self._event_delay(type=SERVER_OUTPUT_UPDATED, resource_id=self.id)

    def push_output(self, output):
        cache_db.list_rpush(self.get_cache_key('output'), output.rstrip('\n'))
        self._event_delay(type=SERVER_OUTPUT_UPDATED, resource_id=self.id)

    def get_bandwidth(self, period=None):
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
            elif period == '5m':
                date_end = date - datetime.timedelta(minutes=date.minute % 5)
                date_cur = date_end - datetime.timedelta(days=1)
                date_step = datetime.timedelta(minutes=5)
            elif period == '30m':
                date_end = date - datetime.timedelta(minutes=date.minute % 30)
                date_cur = date_end - datetime.timedelta(days=7)
                date_step = datetime.timedelta(minutes=30)
            elif period == '2h':
                date_end = date - datetime.timedelta(minutes=date.minute,
                    hours=date.hour % 2)
                date_cur = date_end - datetime.timedelta(days=30)
                date_step = datetime.timedelta(hours=2)
            elif period == '1d':
                date_end = date - datetime.timedelta(minutes=date.minute,
                    hours=date.hour)
                date_cur = date_end - datetime.timedelta(days=365)
                date_step = datetime.timedelta(days=1)

            data_p = {
                'received': [],
                'received_total': 0,
                'sent': [],
                'sent_total': 0,
            }
            data[period] = data_p
            cache_key = self.get_cache_key('bandwidth-%s' % period)

            while date_cur < date_end:
                date_cur += date_step

                timestamp = int(date_cur.strftime('%s'))
                bandwidth = persist_db.dict_get(cache_key, str(timestamp))
                if bandwidth:
                    bandwidth = bandwidth.split(',')
                    bytes_recv = int(bandwidth[0])
                    bytes_sent = int(bandwidth[1])
                else:
                    bytes_recv = 0
                    bytes_sent = 0

                data_p['received'].append((timestamp, bytes_recv))
                data_p['received_total'] += bytes_recv
                data_p['sent'].append((timestamp, bytes_sent))
                data_p['sent_total'] += bytes_sent

        if len(periods) == 1:
            return data[periods[0]]
        else:
            return data

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

        # Store bytes send recv into time periods
        if bytes_recv_t != 0 or bytes_sent_t != 0:
            date = datetime.datetime.utcnow()
            date -= datetime.timedelta(microseconds=date.microsecond,
                seconds=date.second)

            timestamp_1m = date.strftime('%s')
            timestamp_1m_min = int((date - datetime.timedelta(
                hours=6)).strftime('%s'))
            date_5m = date - datetime.timedelta(minutes=date.minute % 5)
            timestamp_5m = date_5m.strftime('%s')
            timestamp_5m_min = int((date_5m - datetime.timedelta(
                days=1)).strftime('%s'))
            date_30m = date - datetime.timedelta(minutes=date.minute % 30)
            timestamp_30m = date_30m.strftime('%s')
            timestamp_30m_min = int((date_30m - datetime.timedelta(
                days=7)).strftime('%s'))
            date_2h = date - datetime.timedelta(
                hours=date.hour % 2, minutes=date.minute)
            timestamp_2h = date_2h.strftime('%s')
            timestamp_2h_min = int((date_2h - datetime.timedelta(
                days=30)).strftime('%s'))
            date_1d = date - datetime.timedelta(
                hours=date.hour, minutes=date.minute)
            timestamp_1d = date_1d.strftime('%s')
            timestamp_1d_min = int((date_1d - datetime.timedelta(
                days=365)).strftime('%s'))

            for period, timestamp, timestamp_min in (
                        ('1m', timestamp_1m, timestamp_1m_min),
                        ('5m', timestamp_5m, timestamp_5m_min),
                        ('30m', timestamp_30m, timestamp_30m_min),
                        ('2h', timestamp_2h, timestamp_2h_min),
                        ('1d', timestamp_1d, timestamp_1d_min),
                    ):
                bytes_recv = bytes_recv_t
                bytes_sent = bytes_sent_t
                prev_bandwidth = persist_db.dict_get(
                    self.get_cache_key('bandwidth-%s' % period), timestamp)
                if prev_bandwidth:
                    prev_bandwidth = prev_bandwidth.split(',')
                    bytes_recv += int(prev_bandwidth[0])
                    bytes_sent += int(prev_bandwidth[1])
                persist_db.dict_set(self.get_cache_key(
                    'bandwidth-%s' % period), timestamp,
                    '%s,%s' % (bytes_recv, bytes_sent))

                for timestamp_p in persist_db.dict_keys(self.get_cache_key(
                        'bandwidth-%s' % period)):
                    if int(timestamp_p) <= timestamp_min:
                        persist_db.dict_remove(self.get_cache_key(
                            'bandwidth-%s' % period), timestamp_p)

    def _read_clients(self):
        clients = {}
        if os.path.isfile(self.ovpn_status_path):
            with open(self.ovpn_status_path, 'r') as status_file:
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
        if force or client_count != len(clients):
            for org in self.iter_orgs():
                Event(type=USERS_UPDATED, resource_id=org.id)
            if not force:
                Event(type=SERVERS_UPDATED)

    @classmethod
    def sort_servers_cache(cls):
        servers_dict = {}
        servers_sort = []

        # Create temp uuid key to prevent multiple threads modifying same key
        temp_sorted_key = 'servers_sorted_temp_' + uuid.uuid4().hex

        try:
            for server_id_type in cache_db.set_elements('servers'):
                server_id, server_type = server_id_type.split('_', 1)
                server = Server.get_server(id=server_id, type=server_type)
                if not server:
                    continue
                name_id = '%s_%s' % (server.name, server_id)
                servers_dict[name_id] = server_id_type
                servers_sort.append(name_id)
            for name_id in sorted(servers_sort):
                cache_db.list_rpush(temp_sorted_key, servers_dict[name_id])
            cache_db.rename(temp_sorted_key, 'servers_sorted')
        except:
            cache_db.remove(temp_sorted_key)
            raise

    @classmethod
    def _cache_servers(cls):
        if cache_db.get('servers_cached') != 't':
            cache_db.remove('servers')
            path = os.path.join(app_server.data_path, SERVERS_DIR)
            if os.path.isdir(path):
                for server_id in os.listdir(path):
                    if not os.path.isfile(os.path.join(path, server_id,
                            SERVER_CONF_NAME)):
                        continue
                    if os.path.isfile(os.path.join(path, server_id,
                            NODE_SERVER)):
                        server_id += '_' + NODE_SERVER
                    else:
                        server_id += '_' + SERVER
                    cache_db.set_add('servers', server_id)
            cls.sort_servers_cache()
            cache_db.set('servers_cached', 't')

    @classmethod
    def get_server(cls, id, type=None):
        from node_server import NodeServer

        if not type:
            if cache_db.set_exists('servers', id + '_' + NODE_SERVER):
                type = NODE_SERVER
            else:
                type = SERVER

        if type == NODE_SERVER:
            server = NodeServer(id=id)
        else:
            server = Server(id=id)
        try:
            server.load()
        except IOError:
            logger.exception('Failed to load server conf. %r' % {
                    'server_id': id,
                })
            return
        return server

    @classmethod
    def iter_servers(cls):
        cls._cache_servers()
        for server_id_type in cache_db.list_iter('servers_sorted'):
            server_id, server_type = server_id_type.split('_', 1)
            server = cls.get_server(id=server_id, type=server_type)
            if server:
                yield server
