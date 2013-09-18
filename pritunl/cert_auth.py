from constants import *
from config import Config
import threading
import uuid
import os
import subprocess

openssl_lock = threading.Lock()

class CertAuth:
    def __init__(self, id=None):
        if id is None:
            self._initialized = False
            self.id = uuid.uuid4().hex
        else:
            self._initialized = True
            self.id = id
        self.path = os.path.join(DATA_DIR, self.id)

        self.index_path = os.path.join(self.path, INDEX_NAME)
        self.index_attr_path = os.path.join(self.path, INDEX_NAME + '.attr')
        self.serial_path = os.path.join(self.path, SERIAL_NAME)
        self.crl_path = os.path.join(self.path, CRL_NAME)

        if not self._initialized:
            self._initialize()

        self.ca_cert = Cert(self, id=CA_CERT_ID)

    def _initialize(self):
        self._make_dirs()
        self.ca_cert = Cert(self, type=CERT_CA)

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

    def get_certs(self):
        certs = []
        for cert_id in os.listdir(os.path.join(self.path, CERTS_DIR)):
            cert_id = cert_id.replace('.crt', '')
            if cert_id == CA_CERT_ID:
                continue
            certs.append(Cert(self, id=cert_id))
        return certs

    def new_cert(self, type, name=None):
        return Cert(self, name=name, type=type)

    def create_crl(self):
        pass

class Cert(Config):
    str_options = ['name']

    def __init__(self, ca, id=None, name=None, type=None):
        Config.__init__(self)
        self.ca = ca
        self.id = id

        if type is not None:
            self.type = type

        if self.id is None:
            if type == CERT_CA:
                self.id = CA_CERT_ID
            elif type is None:
                raise AttributeError('Type must be specified')
            else:
                self.id = uuid.uuid4().hex
            self._initialized = False
        else:
            self._initialized = True

        self.reqs_path = os.path.join(self.ca.path, REQS_DIR,
            '%s.csr' % self.id)
        self.ssl_conf_path = os.path.join(self.ca.path, TEMP_DIR,
            '%s.conf' % self.id)
        self.key_path = os.path.join(self.ca.path, KEYS_DIR,
            '%s.key' % self.id)
        self.cert_path = os.path.join(self.ca.path, CERTS_DIR,
            '%s.crt' % self.id)
        self.set_path(os.path.join(self.ca.path, USERS_DIR,
            '%s.conf' % self.id))

        if name is not None:
            self.name = name

        if not self._initialized:
            self._initialize()

    def __getattr__(self, name):
        if name == 'type':
            self.type = self._load_type()
            return self.type
        return Config.__getattr__(self, name)

    def _initialize(self):
        conf_data = CERT_CONF % (self.ca.id, self.ca.path, self.id)
        with open(self.ssl_conf_path, 'w') as conf_file:
            conf_file.write(conf_data)
        self._cert_request()
        self._cert_create()
        self._delete_conf()
        self.commit()

    def _cert_request(self):
        openssl_lock.acquire()
        try:
            args = [
                'openssl', 'req', '-new', '-batch',
                '-config', self.ssl_conf_path,
                '-out', self.reqs_path,
                '-keyout', self.key_path,
                '-reqexts', '%s_req_ext' % self.type,
            ]
            subprocess.check_call(args)
        finally:
            openssl_lock.release()

    def _cert_create(self):
        openssl_lock.acquire()
        try:
            args = ['openssl', 'ca', '-batch']
            if self.type == CERT_CA:
                args += ['-selfsign']
            args += [
                '-config', self.ssl_conf_path,
                '-in', self.reqs_path,
                '-out', self.cert_path,
                '-extensions', '%s_ext' % self.type,
            ]
            subprocess.check_call(args)
        finally:
            openssl_lock.release()

    def _delete_conf(self):
        os.remove(self.ssl_conf_path)

    def _load_type(self):
        with open(self.cert_path, 'r') as cert_file:
            cert_data = cert_file.read()
            if 'CA:TRUE' in cert_data:
                return CERT_CA
            elif 'TLS Web Server Authentication' in cert_data:
                return CERT_SERVER
            else:
                return  CERT_CLIENT

    def revoke(self):
        pass
