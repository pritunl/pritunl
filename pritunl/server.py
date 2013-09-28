from constants import *
from pritunl import app_server, openssl_lock
from config import Config
from organization import Organization
from event import Event
from log_entry import LogEntry
import uuid
import os
import signal
import time
import shutil
import subprocess
import threading
import logging

logger = logging.getLogger(APP_NAME)
_threads = {}
_output = {}
_process = {}
_start_time = {}

class Server(Config):
    str_options = ['name', 'network', 'interface', 'protocol',
        'local_network', 'public_address', 'primary_organization',
        'primary_user', 'organizations']
    int_options = ['port']
    list_options = ['organizations']

    def __init__(self, id=None, name=None, network=None, interface=None,
            port=None, protocol=None, local_network=None, public_address=None,
            organizations=[]):
        Config.__init__(self)
        self._cur_event = None
        self._last_event = 0

        if id is None:
            self._initialized = False
            self.id = uuid.uuid4().hex
            self.name = name
            self.network = network
            self.interface = interface
            self.port = port
            self.protocol = protocol
            self.local_network = local_network
            self.public_address = public_address
            self.organizations = organizations
        else:
            self._initialized = True
            self.id = id

        self.path = os.path.join(app_server.data_path, SERVERS_DIR, self.id)
        self.ovpn_conf_path = os.path.join(self.path, TEMP_DIR, OVPN_CONF_NAME)
        self.dh_param_path = os.path.join(self.path, DH_PARAM_NAME)
        self.ifc_pool_path = os.path.join(self.path, IFC_POOL_NAME)
        self.ca_cert_path = os.path.join(self.path, TEMP_DIR, OVPN_CA_NAME)
        self.ovpn_status_path = os.path.join(self.path, TEMP_DIR,
            OVPN_STATUS_NAME)
        self.set_path(os.path.join(self.path, 'server.conf'))

        if not self._initialized:
            self._initialize()

    def __getattr__(self, name):
        if name == 'status':
            if self.id in _threads:
                return _threads[self.id].is_alive()
            return False
        elif name == 'uptime':
            if self.status and self.id in _start_time:
                return int(time.time()) - _start_time[self.id]
            return None

        return Config.__getattr__(self, name)

    def _initialize(self):
        logging.info('Initialize new server. %r' % {
            'server_id': self.id,
        })
        os.makedirs(os.path.join(self.path, TEMP_DIR))
        self._generate_dh_param()
        self.commit()
        LogEntry(message='Created new server.')

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
        logging.info('Removing server. %r' % {
            'server_id': self.id,
        })
        self._remove_primary_user()
        shutil.rmtree(self.path)
        LogEntry(message='Deleted server.')
        Event(type=SERVERS_UPDATED)

    def commit(self):
        Config.commit(self)
        Event(type=SERVERS_UPDATED)

    def _create_primary_user(self):
        if not self.organizations:
            raise ValueError('Primary user cannot be created without ' + \
                'any organizations')
        logging.debug('Creating primary user. %r' % {
            'server_id': self.id,
        })
        org = Organization(self.organizations[0])
        self.primary_organization = org.id
        user = org.new_user(CERT_SERVER, SERVER_USER_PREFIX + self.id)
        self.primary_user = user.id
        try:
            self.commit()
        except:
            user.remove()
            raise

    def add_org(self, org_id):
        logging.debug('Adding organization to server. %r' % {
            'server_id': self.id,
            'org_id': org_id,
        })
        org = Organization(org_id)
        if org.id in self.organizations:
            return
        self.organizations.append(org.id)
        self.commit()
        Event(type=SERVERS_UPDATED)
        Event(type=SERVER_ORGS_UPDATED, resource_id=self.id)

    def _remove_primary_user(self):
        logging.debug('Removing primary user. %r' % {
            'server_id': self.id,
            'org_id': org_id,
        })

        primary_organization = self.primary_organization
        primary_user = self.primary_user
        self.primary_organization = None
        self.primary_user = None

        if not primary_organization or not primary_user:
            return

        org = Organization(primary_organization)
        if not org:
            return

        user = org.get_user(primary_user)
        if not user:
            return

        if user:
            user.remove()

    def remove_org(self, org_id):
        if org_id not in self.organizations:
            return
        logging.debug('Removing organization from server. %r' % {
            'server_id': self.id,
            'org_id': org_id,
        })
        if self.primary_organization == org_id:
            self._remove_primary_user()
        self.organizations.remove(org_id)
        self.commit()
        Event(type=SERVERS_UPDATED)
        Event(type=SERVER_ORGS_UPDATED, resource_id=self.id)

    def _generate_dh_param(self):
        logging.debug('Generating server dh params. %r' % {
            'server_id': self.id,
        })
        args = [
            'openssl', 'dhparam',
            '-out', self.dh_param_path, str(DH_PARAM_BITS)
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
        logging.debug('Generating server ca cert. %r' % {
            'server_id': self.id,
        })
        with open(self.ca_cert_path, 'w') as server_ca_cert:
            for org_id in self.organizations:
                ca_path = Organization(org_id).ca_cert.cert_path
                with open(ca_path, 'r') as org_ca_cert:
                    server_ca_cert.write(org_ca_cert.read())

    def _generate_ovpn_conf(self):
        if not self.organizations:
            raise ValueError('Ovpn conf cannot be generated without ' + \
                'any organizations')

        logging.debug('Generating server ovpn conf. %r' % {
            'server_id': self.id,
        })

        if not self.primary_organization or not self.primary_user:
            self._create_primary_user()

        if not os.path.isfile(self.dh_param_path):
            self._generate_dh_param()

        primary_org = Organization(self.primary_organization)
        primary_user = primary_org.get_user(self.primary_user)

        self.generate_ca_cert()

        if self.local_network:
            push = 'route %s %s' % self._parse_network(
                self.local_network)
        else:
            push = 'redirect-gateway'

        with open(self.ovpn_conf_path, 'w') as ovpn_conf:
            ovpn_conf.write(OVPN_SERVER_CONF % (
                self.port,
                self.protocol,
                self.interface,
                self.ca_cert_path,
                primary_user.cert_path,
                primary_user.key_path,
                self.dh_param_path,
                '%s %s' % self._parse_network(self.network),
                self.ifc_pool_path,
                push,
                self.ovpn_status_path,
            ))

    def _run(self):
        logging.debug('Starting ovpn process. %r' % {
            'server_id': self.id,
        })
        process = subprocess.Popen(['openvpn', self.ovpn_conf_path],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        _process[self.id] = process

        while True:
            line = process.stdout.readline()
            if line == '' and process.poll() is not None:
                break
            _output[self.id] += line
            self._event_delay(type=SERVER_OUTPUT_UPDATED, resource_id=self.id)

        del _threads[self.id]
        del _process[self.id]
        del _start_time[self.id]
        Event(type=SERVERS_UPDATED)

    def start(self):
        if not self.organizations:
            raise ValueError('Server cannot be started without ' + \
                'any organizations')
        logging.debug('Starting server. %r' % {
            'server_id': self.id,
        })
        self._generate_ovpn_conf()
        thread = threading.Thread(target=self._run)
        thread.start()
        _threads[self.id] = thread
        _start_time[self.id] = int(time.time()) - 1
        _output[self.id] = ''
        Event(type=SERVERS_UPDATED)

    def stop(self):
        if not self.status:
            raise ValueError('Server is not running')
        logging.debug('Stopping server. %r' % {
            'server_id': self.id,
        })
        _process[self.id].send_signal(signal.SIGINT)

    def restart(self):
        if not self.status:
            raise ValueError('Server is not running')
        logging.debug('Restarting server. %r' % {
            'server_id': self.id,
        })
        _process[self.id].send_signal(signal.SIGHUP)

    def reload(self):
        if not self.status:
            raise ValueError('Server is not running')
        logging.debug('Reloading server. %r' % {
            'server_id': self.id,
        })
        _process[self.id].send_signal(signal.SIGUSR1)

    def get_output(self):
        if self.id not in _output:
            return ''
        return _output[self.id]

    @staticmethod
    def count_servers():
        logging.debug('Counting servers.')
        return len(os.listdir(os.path.join(app_server.data_path, SERVERS_DIR)))

    @staticmethod
    def get_servers():
        logging.debug('Getting servers.')
        path = os.path.join(app_server.data_path, SERVERS_DIR)
        servers = []
        if os.path.isdir(path):
            for server_id in os.listdir(path):
                servers.append(Server(server_id))
        return servers
