from constants import *
from pritunl import app_server
from cache import cache_db
from cache_trie import CacheTrie
from config import Config
from event import Event
from log_entry import LogEntry
from user import User
import uuid
import os
import subprocess
import utils
import logging
import threading

logger = logging.getLogger(APP_NAME)

class Organization(Config):
    str_options = {'name'}
    cached = True
    cache_prefix = 'org'

    def __init__(self, id=None, name=None):
        Config.__init__(self)
        self._last_prefix_count = None

        if id is None:
            self.id = uuid.uuid4().hex
            self.name = name
        else:
            self.id = id

        self.path = os.path.join(app_server.data_path, ORGS_DIR, self.id)
        self.set_path(os.path.join(self.path, 'ca.conf'))

        if id is None:
            self._initialize()

        self.ca_cert = User.get_user(self, id=CA_CERT_ID)

    def __getattr__(self, name):
        if name == 'otp_auth':
            for server in self.iter_servers():
                if server.otp_auth:
                    return True
            return False
        elif name == 'user_count':
            return self._get_user_count()
        elif name == 'page_total':
            return int(cache_db.get(self.get_cache_key('users_page_total')))
        return Config.__getattr__(self, name)

    def dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'user_count': self.user_count,
        }

    def _upgrade_0_10_5(self):
        logger.debug('Upgrading org to v0.10.5... %r' % {
            'org_id': self.id,
        })
        for path in [
                os.path.join(self.path, INDEX_NAME),
                os.path.join(self.path, INDEX_NAME + '.old'),
                os.path.join(self.path, INDEX_ATTR_NAME),
                os.path.join(self.path, INDEX_ATTR_NAME + '.old'),
                os.path.join(self.path, SERIAL_NAME),
                os.path.join(self.path, SERIAL_NAME + '.old'),
                os.path.join(self.path, 'ca.crl'),
            ]:
            try:
                os.remove(path)
            except OSError:
                pass
        utils.rmtree(os.path.join(self.path, 'indexed_certs'))

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
        os.makedirs(os.path.join(self.path, USERS_DIR))
        os.makedirs(os.path.join(self.path, TEMP_DIR))

    def clear_cache(self):
        cache_db.set_remove('orgs', self.id)
        cache_db.list_remove('orgs_sorted', self.id)
        cache_db.decrement('org_count')
        cache_db.remove(self.get_cache_key('users_cached'))
        cache_db.remove(self.get_cache_key('users'))
        Config.clear_cache(self)

    def get_user(self, id):
        return User.get_user(self, id=id)

    def sort_users_cache(self):
        user_count = 0
        users_dict = {}
        users_sort = []

        # Create temp uuid key to prevent multiple threads modifying same key
        temp_suffix = 'temp_' + uuid.uuid4().hex
        temp_users_sorted_key = 'users_sorted_' + temp_suffix
        users_page_index_key = 'users_page_index_' + temp_suffix

        try:
            for user_id in cache_db.set_elements(self.get_cache_key('users')):
                user = User.get_user(self, id=user_id)
                if not user:
                    continue
                name_id = '%s_%s' % (user.name, user_id)
                if user.type == CERT_CLIENT:
                    user_count += 1
                users_dict[name_id] = (user_id, user.type)
                users_sort.append(name_id)

            cache_db.set(self.get_cache_key('user_count'), str(user_count))

            cur_page = 0
            user_count = 0
            client_count = 0
            for name_id in sorted(users_sort):
                if users_dict[name_id][1] == CERT_CLIENT:
                    page = client_count / USER_PAGE_COUNT
                    if page != cur_page:
                        cur_page = page
                        cache_db.dict_set(self.get_cache_key(users_page_index_key),
                            str(cur_page), str(user_count))
                    client_count += 1
                user_count += 1
                cache_db.list_rpush(self.get_cache_key(temp_users_sorted_key),
                    users_dict[name_id][0])

            cache_db.lock_acquire(self.get_cache_key('sort'))
            try:
                cache_db.rename(self.get_cache_key(users_page_index_key),
                    self.get_cache_key('users_page_index'))
                cache_db.rename(self.get_cache_key(temp_users_sorted_key),
                    self.get_cache_key('users_sorted'))
                cache_db.set(self.get_cache_key('users_page_total'),
                    str(cur_page))
            finally:
                cache_db.lock_release(self.get_cache_key('sort'))
        except:
            cache_db.remove(self.get_cache_key(users_page_index_key))
            cache_db.remove(self.get_cache_key(temp_users_sorted_key))
            raise

    def _cache_users(self):
        if cache_db.get(self.get_cache_key('users_cached')) != 't':
            users_trie = CacheTrie(self.get_cache_key('users_trie'))
            cache_db.remove(self.get_cache_key('users'))
            certs_path = os.path.join(self.path, CERTS_DIR)
            if os.path.isdir(certs_path):
                for cert in os.listdir(certs_path):
                    user_id = cert.replace('.crt', '')
                    if user_id == CA_CERT_ID:
                        continue
                    user = User.get_user(self, id=user_id)
                    if not user:
                        continue
                    users_trie.add_key(user.name, user_id)
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

    def iter_users(self, page=None, prefix=None, prefix_limit=None):
        self._cache_users()
        if page is not None:
            page_total = self.page_total
            page = min(page, page_total)
            if page == 0:
                page_index_s = 0
            else:
                page_index_s = int(cache_db.dict_get(self.get_cache_key(
                    'users_page_index'), str(page)))

            if page == page_total:
                page_index_e = None
            else:
                page_index_e = int(cache_db.dict_get(self.get_cache_key(
                    'users_page_index'), str(page + 1)))

            for user_id in cache_db.list_iter_range(
                    self.get_cache_key('users_sorted'),
                    page_index_s, page_index_e):
                user = User.get_user(self, id=user_id)
                if user:
                    yield user
        elif prefix is not None:
            users_dict = {}
            users_sort = []
            prefix_count = 0
            users_trie = CacheTrie(self.get_cache_key('users_trie'))
            for user_id in users_trie.iter_prefix(prefix):
                user = User.get_user(self, id=user_id)
                if not user:
                    continue
                if user.type == CERT_CLIENT:
                    prefix_count  += 1
                name_id = '%s_%s' % (user.name, user_id)
                users_dict[name_id] = user
                users_sort.append(name_id)
            self._last_prefix_count = prefix_count

            user_count = 0
            search_more = False
            for name_id in sorted(users_sort):
                yield users_dict[name_id]
                if prefix_limit:
                    if users_dict[name_id].type == CERT_CLIENT:
                        user_count += 1
                        if user_count >= prefix_limit:
                            search_more = True
                            break
            if prefix_limit and not search_more:
                yield None
        else:
            for user_id in cache_db.list_iter(
                    self.get_cache_key('users_sorted')):
                user = User.get_user(self, id=user_id)
                if user:
                    yield user

    def get_last_prefix_count(self):
        return self._last_prefix_count

    def get_server(self, server_id):
        from server import Server
        server = Server.get_server(id=server_id)
        if self.id in server.organizations:
            return server

    def iter_servers(self):
        from server import Server
        for server in Server.iter_servers():
            if self.id in server.organizations:
                yield server

    def new_user(self, type, name=None):
        return User(self, name=name, type=type)

    def rename(self, name):
        self.name = name
        self.commit()
        self.sort_orgs_cache()
        Event(type=ORGS_UPDATED)

    def remove(self):
        self.clear_cache()
        name = self.name

        for server in self.iter_servers():
            if server.status:
                server.stop()
            server.remove_org(self.id)

        utils.rmtree(self.path)
        LogEntry(message='Deleted organization "%s".' % name)
        Event(type=ORGS_UPDATED)

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

        # Create temp uuid key to prevent multiple threads modifying same key
        temp_orgs_sorted_key = 'orgs_sorted_temp_' + uuid.uuid4().hex

        try:
            for org_id in cache_db.set_elements('orgs'):
                org = Organization.get_org(id=org_id)
                if not org:
                    continue
                name_id = '%s_%s' % (org.name, org_id)
                org_count += 1
                orgs_dict[name_id] = org_id
                orgs_sort.append(name_id)
            cache_db.set('org_count', str(org_count))
            for name_id in sorted(orgs_sort):
                cache_db.list_rpush(temp_orgs_sorted_key, orgs_dict[name_id])
            cache_db.rename(temp_orgs_sorted_key, 'orgs_sorted')
        except:
            cache_db.remove(self.get_cache_key(temp_orgs_sorted_key))
            raise

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
        for org_id in cache_db.list_iter('orgs_sorted'):
            org = Organization.get_org(id=org_id)
            if org:
                yield org
