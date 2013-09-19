from constants import *
from pritunl import server, openssl_lock
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
        self.path = os.path.join(server.data_path, self.id)

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

    def count_users(self):
        certs_path = os.path.join(self.path, CERTS_DIR)
        if not os.path.isdir(certs_path):
            return 0
        return len(os.listdir(certs_path))

    def get_user(self, id):
        return User(self, id=id)

    def new_user(self, type, name=None):
        return User(self, name=name, type=type)

    def generate_crl(self):
        openssl_lock.acquire()
        try:
            conf_path = os.path.join(self.path, TEMP_DIR, 'crl.conf')
            conf_data = CERT_CONF % (self.id, self.path, CA_CERT_ID)
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
        finally:
            openssl_lock.release()

    def rename(self, name):
        self.name = name
        self.commit()
        Event(type=ORGS_UPDATED)

    def remove(self):
        shutil.rmtree(self.path)
        Event(type=ORGS_UPDATED)
        LogEntry(message='Deleted organization.')

    @staticmethod
    def count_orgs():
        return len(os.listdir(server.data_path))

    @staticmethod
    def get_orgs():
        orgs = []
        if os.path.isdir(server.data_path):
            for org_id in os.listdir(server.data_path):
                orgs.append(Organization(org_id))
        return orgs
