from constants import *
from pritunl import app_server, openssl_lock
from config import Config
from event import Event
from log_entry import LogEntry
from user import User
import uuid
import os
import shutil
import subprocess

class Organization(Config):
    str_options = ['name']

    def __init__(self, id=None, name=None):
        Config.__init__(self)

        if id is None:
            self._initialized = False
            self.id = uuid.uuid4().hex
        else:
            self._initialized = True
            self.id = id
        self.path = os.path.join(app_server.data_path, ORGS_DIR, self.id)

        self.index_path = os.path.join(self.path, INDEX_NAME)
        self.index_attr_path = os.path.join(self.path, INDEX_NAME + '.attr')
        self.serial_path = os.path.join(self.path, SERIAL_NAME)
        self.crl_path = os.path.join(self.path, CRL_NAME)
        self.set_path(os.path.join(self.path, 'ca.conf'))

        if name is not None:
            self.name = name

        if not self._initialized:
            self._initialize()

        self.ca_cert = User(self, id=CA_CERT_ID)

    def _initialize(self):
        self._make_dirs()
        self.ca_cert = User(self, type=CERT_CA)
        self.commit()
        LogEntry(message='Created new organization.')
        Event(type=ORGS_UPDATED)

    def _make_dirs(self):
        os.makedirs(os.path.join(self.path, REQS_DIR))
        os.makedirs(os.path.join(self.path, KEYS_DIR), 0700)
        os.makedirs(os.path.join(self.path, CERTS_DIR))
        os.makedirs(os.path.join(self.path, INDEXED_CERTS_DIR))
        os.makedirs(os.path.join(self.path, USERS_DIR))
        os.makedirs(os.path.join(self.path, TEMP_DIR))

        with open(self.index_path, 'a'):
            os.utime(self.index_path, None)

        with open(self.index_attr_path, 'a'):
            os.utime(self.index_attr_path, None)

        with open(self.serial_path, 'w') as serial_file:
            serial_file.write('01\n')

    def get_user(self, id):
        return User(self, id=id)

    def get_users(self):
        users = []
        certs_path = os.path.join(self.path, CERTS_DIR)
        if os.path.isdir(certs_path):
            for user_id in os.listdir(certs_path):
                user_id = user_id.replace('.crt', '')
                if user_id == CA_CERT_ID:
                    continue
                users.append(User(self, id=user_id))
        return users

    def get_servers(self):
        from server import Server
        servers = []

        for server in Server.get_servers():
            if self.id in server.organizations:
                servers.append(server)

        return servers

    def new_user(self, type, name=None):
        return User(self, name=name, type=type)

    def generate_crl(self):
        openssl_lock.acquire()
        try:
            conf_path = os.path.join(self.path, TEMP_DIR, 'crl.conf')
            conf_data = CERT_CONF % (self.id, self.path,
                app_server.key_bits, CA_CERT_ID)
            with open(conf_path, 'w') as conf_file:
                conf_file.write(conf_data)
            args = [
                'openssl', 'ca', '-gencrl', '-batch',
                '-config', conf_path,
                '-out', self.crl_path
            ]
            subprocess.check_call(args, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
            os.remove(conf_path)
        except subprocess.CalledProcessError:
            logger.exception('Failed to generate server crl. %r' % {
                'org_id': self.id,
            })
            raise
        finally:
            openssl_lock.release()

    def rename(self, name):
        self.name = name
        self.commit()
        Event(type=ORGS_UPDATED)

    def remove(self):
        for server in self.get_servers():
            if server.status:
                server.stop()
            server.remove_org(self.id)

        shutil.rmtree(self.path)
        LogEntry(message='Deleted organization.')
        Event(type=ORGS_UPDATED)

    @staticmethod
    def get_orgs():
        path = os.path.join(app_server.data_path, ORGS_DIR)
        orgs = []
        if os.path.isdir(path):
            for org_id in os.listdir(path):
                orgs.append(Organization(org_id))
        return orgs
