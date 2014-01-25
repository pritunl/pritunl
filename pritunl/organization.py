from constants import *
from pritunl import app_server
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

        self.ca_cert = User.get_user(self, id=CA_CERT_ID)

    def __getattr__(self, name):
        if name == 'otp_auth':
            for server in self.get_servers():
                if server.otp_auth:
                    return True
            return False
        elif name == 'user_count':
            return self._get_user_count()
        return Config.__getattr__(self, name)

    def dict(self):
        return {
            'id': self.id,
            'name': self.name,
        }

    def _initialize(self):
        self._make_dirs()
        self.ca_cert = User(self, type=CERT_CA)
        self.commit()
        cache_db.set_add('orgs', self.id)
        self.sort_orgs_cache()
        LogEntry(message='Created new organization "%s".' % self.name)
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

    def clear_cache(self):
        cache_db.set_remove('orgs', self.id)
        cache_db.list_remove(self.get_cache_key('orgs_sorted'), self.id)
        cache_db.decrement(self.get_cache_key('org_count'))
        cache_db.remove(self.get_cache_key('users_cached'))
        cache_db.remove(self.get_cache_key('users'))
        Config.clear_cache(self)

    def get_user(self, id):
        return User.get_user(self, id=id)

    def sort_users_cache(self):
        user_count = 0
        users_dict = {}
        users_sort = []
        for user_id in cache_db.set_elements(self.get_cache_key('users')):
            user = User.get_user(self, id=user_id)
            if not user:
                continue
            name_id = '%s_%s' % (user.name, user_id)
            if user.type == CERT_CLIENT:
                user_count += 1
            users_dict[name_id] = user_id
            users_sort.append(name_id)
        cache_db.set(self.get_cache_key('user_count'), str(user_count))
        cache_db.remove(self.get_cache_key('users_sorted_temp'))
        for name_id in sorted(users_sort):
            cache_db.list_rpush(self.get_cache_key('users_sorted_temp'),
                users_dict[name_id])
        cache_db.rename(self.get_cache_key('users_sorted_temp'),
            self.get_cache_key('users_sorted'))

    def _cache_users(self):
        if cache_db.get(self.get_cache_key('users_cached')) != 't':
            cache_db.remove(self.get_cache_key('users'))
            certs_path = os.path.join(self.path, CERTS_DIR)
            if os.path.isdir(certs_path):
                for cert in os.listdir(certs_path):
                    user_id = cert.replace('.crt', '')
                    if user_id == CA_CERT_ID:
                        continue
                    cache_db.set_add(self.get_cache_key('users'), user_id)
            self.sort_users_cache()
            cache_db.set(self.get_cache_key('users_cached'), 't')

    def _get_user_count(self):
        try:
            user_count = int(cache_db.get(self.get_cache_key('user_count')))
        except TypeError:
            self._cache_users()
            user_count = int(cache_db.get(self.get_cache_key('user_count')))
        return user_count

    def iter_users(self):
        self._cache_users()
        for user_id in cache_db.list_elements(self.get_cache_key(
                'users_sorted')):
            user = User.get_user(self, id=user_id)
            if user:
                yield user

    def get_server(self, server_id):
        from server import Server
        server = Server.get_server(id=server_id)
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
        return User(self, name=name, type=type)

    def generate_crl(self):
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

    def rename(self, name):
        self.name = name
        self.commit()
        self.sort_orgs_cache()
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

    @classmethod
    def get_org(cls, id):
        org = Organization(id=id)
        try:
            org.load()
        except IOError:
            logger.exception('Failed to load organization conf. %r' % {
                'org_id': id,
            })
            return
        return org

    @classmethod
    def sort_orgs_cache(cls):
        org_count = 0
        orgs_dict = {}
        orgs_sort = []
        for org_id in cache_db.set_elements('orgs'):
            org = Organization.get_org(id=org_id)
            if not org:
                continue
            name_id = '%s_%s' % (org.name, org_id)
            org_count += 1
            orgs_dict[name_id] = org_id
            orgs_sort.append(name_id)
        cache_db.set('org_count', str(org_count))
        cache_db.remove('orgs_sorted_temp')
        for name_id in sorted(orgs_sort):
            cache_db.list_rpush('orgs_sorted_temp', orgs_dict[name_id])
        cache_db.rename('orgs_sorted_temp', 'orgs_sorted')

    @classmethod
    def _cache_orgs(cls):
        if cache_db.get('orgs_cached') != 't':
            cache_db.remove('orgs')
            path = os.path.join(app_server.data_path, ORGS_DIR)
            if os.path.isdir(path):
                for org_id in os.listdir(path):
                    cache_db.set_add('orgs', org_id)
            cls.sort_orgs_cache()
            cache_db.set('orgs_cached', 't')

    @classmethod
    def get_org_count(cls):
        try:
            org_count = int(cache_db.get('org_count'))
        except TypeError:
            self._cache_orgs()
            org_count = int(cache_db.get('org_count'))
        return org_count

    @classmethod
    def iter_orgs(cls):
        cls._cache_orgs()
        for org_id in cache_db.list_elements('orgs_sorted'):
            org = Organization.get_org(id=org_id)
            if org:
                yield org
