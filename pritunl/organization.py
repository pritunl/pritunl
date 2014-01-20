from constants import *
from pritunl import app_server, openssl_lock
from cache import cache_db
from config import Config
from event import Event
from log_entry import LogEntry
from user import User
import uuid
import os
import subprocess
import utils
import logging

logger = logging.getLogger(APP_NAME)

class Organization(Config):
    str_options = {'name'}
    cached = True
    cache_prefix = 'org'

    def __init__(self, id=None, name=None):
        Config.__init__(self)

        if id is None:
            self.id = uuid.uuid4().hex
            self.name = name
        else:
            self.id = id

        self.path = os.path.join(app_server.data_path, ORGS_DIR, self.id)
        self.index_path = os.path.join(self.path, INDEX_NAME)
        self.index_attr_path = os.path.join(self.path, INDEX_NAME + '.attr')
        self.serial_path = os.path.join(self.path, SERIAL_NAME)
        self.crl_path = os.path.join(self.path, CRL_NAME)
        self.set_path(os.path.join(self.path, 'ca.conf'))

        if id is None:
            self._initialize()

        self.ca_cert = User(self, id=CA_CERT_ID)

    def __getattr__(self, name):
        if name == 'otp_auth':
            for server in self.get_servers():
                if server.otp_auth:
                    return True
            return False
        return Config.__getattr__(self, name)

    def _initialize(self):
        self._make_dirs()
        self.ca_cert = User(self, type=CERT_CA)
        self.commit()
        LogEntry(message='Created new organization "%s".' % self.name)
        Event(type=ORGS_UPDATED)
        cache_db.set_add('orgs', self.id)

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

    def clear_cache(self):
        cache_db.set_remove('orgs', self.id)
        cache_db.remove(self.get_cache_key('users_cached'))
        cache_db.remove(self.get_cache_key('users'))
        Config.clear_cache(self)

    def get_user(self, id):
        user = User(self, id=id)
        try:
            user.load()
        except IOError:
            logger.exception('Failed to load user conf. %r' % {
                    'org_id': self.id,
                    'user_id': id,
                })
            return
        return user

    def get_users(self):
        if cache_db.get(self.get_cache_key('users_cached')) != 't':
            certs_path = os.path.join(self.path, CERTS_DIR)
            if os.path.isdir(certs_path):
                for cert in os.listdir(certs_path):
                    user_id = cert.replace('.crt', '')
                    if user_id == CA_CERT_ID:
                        continue
                    cache_db.set_add(self.get_cache_key('users'), user_id)
            cache_db.set(self.get_cache_key('users_cached'), 't')

        users = []
        for user_id in cache_db.set_elements(self.get_cache_key('users')):
            user = User(self, id=user_id)
            try:
                user.load()
            except IOError:
                logger.exception('Failed to load user conf, ' +
                    'ignoring user. %r' % {
                        'org_id': self.id,
                        'user_id': user_id,
                    })
                continue
            users.append(user)
        return users

    def get_server(self, server_id):
        from server import Server
        server = Server(server_id)
        if self.id in server.organizations:
            return server

    def get_servers(self):
        from server import Server
        servers = []

        for server in Server.get_servers():
            if self.id in server.organizations:
                servers.append(server)

        return servers

    def new_user(self, type, name=None):
        user = User(self, name=name, type=type)
        cache_db.set_add(self.get_cache_key('users'), user.id)
        return user

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
        name = self.name

        for server in self.get_servers():
            if server.status:
                server.stop()
            server.remove_org(self.id)

        utils.rmtree(self.path)
        LogEntry(message='Deleted organization "%s".' % name)
        Event(type=ORGS_UPDATED)
        self.clear_cache()

    @staticmethod
    def get_orgs():
        if cache_db.get('orgs_cached') != 't':
            path = os.path.join(app_server.data_path, ORGS_DIR)
            if os.path.isdir(path):
                for org_id in os.listdir(path):
                    cache_db.set_add('orgs', org_id)
            cache_db.set('orgs_cached', 't')

        orgs = []
        for org_id in cache_db.set_elements('orgs'):
            org = Organization(org_id)
            try:
                org.load()
            except IOError:
                logger.exception('Failed to load organization conf, ' +
                    'ignoring organization. %r' % {
                        'org_id': org_id,
                    })
                continue
            orgs.append(org)
        return orgs
