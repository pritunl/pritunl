from constants import *
from pritunl import app_server, openssl_lock
from config import Config
from pritunl.organization import Organization
from event import Event
from log_entry import LogEntry
from user import User
import uuid
import os
import shutil
import subprocess

class Server(Config):
    str_options = ['name', 'network', 'interface', 'protocol',
        'local_network', 'primary_organization', 'primary_user',
        'organizations']
    int_options = ['port']
    list_options = ['organizations']

    def __init__(self, id=None, name=None, network=None, interface=None,
            port=None, protocol=None, local_network=None, organizations=[]):
        Config.__init__(self)

        if id is None:
            self._initialized = False
            self.id = uuid.uuid4().hex
            self.name = name
            self.network = network
            self.interface = interface
            self.port = port
            self.protocol = protocol
            self.local_network = local_network
            self.organizations = organizations
        else:
            self._initialized = True
            self.id = id

        self.path = os.path.join(app_server.data_path, SERVERS_DIR, self.id)
        self.ovpn_conf_path = os.path.join(self.path, OVPN_CONF_NAME)
        self.set_path(os.path.join(self.path, 'server.conf'))

        if not self._initialized:
            self._initialize()

    def _initialize(self):
        os.makedirs(self.path)
        self.commit()
        LogEntry(message='Created new server.')

    def remove(self):
        shutil.rmtree(self.path)
        LogEntry(message='Deleted server.')
        Event(type=SERVERS_UPDATED)

    def commit(self):
        Config.commit(self)
        Event(type=SERVERS_UPDATED)

    def _create_primary_user(self):
        if not self.organizations:
            return
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
        org = Organization(org_id)

        if org.id in self.organizations:
            return
        self.organizations.append(org.id)

        if not self.primary_organization or self.primary_user:
            self._create_primary_user()
        else:
            self.commit()
        Event(type=SERVER_ORGS_UPDATED)

    def remove_org(self, org_id):
        if org_id in self.organizations:
            if self.primary_organization == org_id:
                org = Organization(self.primary_organization)
                user = org.get_user(self.primary_user)
                if user:
                    user.remove()
            self.organizations.remove(org_id)
            self.commit()
            Event(type=SERVER_ORGS_UPDATED)

    @staticmethod
    def count_servers():
        return len(os.listdir(os.path.join(app_server.data_path, SERVERS_DIR)))

    @staticmethod
    def get_servers():
        path = os.path.join(app_server.data_path, SERVERS_DIR)
        servers = []
        if os.path.isdir(path):
            for server_id in os.listdir(path):
                servers.append(Server(server_id))
        return servers
