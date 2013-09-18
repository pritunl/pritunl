from constants import *
from pritunl import openssl_lock
from config import Config
from event import Event
import uuid
import os
import subprocess

class User(Config):
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
        self._create_ssl_conf()
        self._cert_request()
        self._cert_create()
        self._delete_ssl_conf()
        self.commit()
        Event(type=USERS_UPDATED)

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

    def _create_ssl_conf(self):
        conf_data = CERT_CONF % (self.ca.id, self.ca.path, self.id)
        with open(self.ssl_conf_path, 'w') as conf_file:
            conf_file.write(conf_data)

    def _delete_ssl_conf(self):
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

    def revoke(self, reason=UNSPECIFIED):
        if self.id == CA_CERT_ID:
            raise TypeError('Cannot revoke ca cert')
        openssl_lock.acquire()
        try:
            self._create_ssl_conf()
            args = ['openssl', 'ca', '-batch',
                '-config', self.ssl_conf_path,
                '-revoke', self.cert_path,
                '-crl_reason', reason
            ]
            subprocess.check_call(args)
            self._delete_ssl_conf()
        finally:
            openssl_lock.release()
