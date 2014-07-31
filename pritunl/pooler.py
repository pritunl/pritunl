from constants import *
from exceptions import *
from pritunl import app_server
from cache import cache_db, persist_db
from organization import Organization
import logging
import time
import threading
import uuid
import subprocess
import os
import itertools

logger = logging.getLogger(APP_NAME)

class Pooler:
    def __init__(self):
        self._orgs_users_thread = None
        self._servers_thread = None

        self.dh_pool_path = os.path.join(app_server.data_path, DH_POOL_DIR)
        if not os.path.exists(self.dh_pool_path):
            os.makedirs(self.dh_pool_path)

        for dh_param in os.listdir(self.dh_pool_path):
            dh_param_path = os.path.join(self.dh_pool_path, dh_param)

            dh_param_split = dh_param.split('_')
            if len(dh_param_split) != 2:
                logger.warning(
                    'Invalid dh param name in pool, skipping... %r' % {
                        'path': dh_param_path
                    })
                continue

            dh_param_bits, dh_param_id = dh_param_split
            try:
                dh_param_bits = int(dh_param_bits)
            except ValueError:
                logger.warning(
                    'Invalid dh param size in pool, skipping... %r' % {
                        'path': dh_param_path
                    })
                continue

            if dh_param_bits not in VALID_DH_PARAM_BITS:
                logger.warning(
                    'Unknown dh param size in pool, skipping... %r' % {
                        'path': dh_param_path
                    })
                continue

            if len(dh_param_id) != 32 or not dh_param_id.isalnum() or \
                    not dh_param_id.islower():
                logger.warning(
                    'Invalid dh param id in pool, skipping... %r' % {
                        'path': dh_param_path
                    })
                continue

            cache_db.dict_set('dh_pool_state', dh_param_path, COMPLETE)
            cache_db.set_add('dh_pool_%s' % dh_param_bits, dh_param_path)

    def _fill_orgs_pool(self):
        for _ in xrange(app_server.org_pool_size -
                Organization.get_org_pool_count()):
            Organization(pool=True)

    def _fill_users_pool(self):
        end = True
        for org in itertools.chain(Organization.iter_orgs(),
                Organization.iter_orgs_pool()):
            if app_server.user_pool_size - org.client_pool_count > 0:
                end = False
                org.new_user(type=CERT_CLIENT_POOL)
            if app_server.server_user_pool_size - org.server_pool_size > 0:
                end = False
                org.new_user(type=CERT_SERVER_POOL)
        if not end:
            self._fill_users_pool()

    def _fill_orgs_users(self):
        retry = False
        try:
            self._fill_orgs_pool()
        except:
            logger.exception('Error filling orgs pool, retying...')
            retry = True

        try:
            self._fill_users_pool()
        except:
            # Exception can occur when org is deleted whiling filling
            logger.debug('Error filling users pool, retying...')
            retry = True

        if retry:
            time.sleep(3)
            self._fill_orgs_users()

    def _fill_orgs_users_thread(self):
        self._fill_orgs_users()

        for msg in cache_db.subscribe('users_pool'):
            if msg == 'update':
                self._fill_orgs_users()

    def _fill_servers_pool_listener(self, cache_key, dh_param_path, process):
        for msg in cache_db.subscribe('dh_pooler'):
            if msg == 'poll':
                if process.poll() is not None:
                    break
                elif cache_db.set_length('dh_param_tasks') and \
                        cache_db.set_exists(cache_key, dh_param_path):
                    # There is a running dhparam process started by the user
                    # which takes priority over the pooler's dhparam process
                    if process.poll() is None:
                        process.terminate()
                        time.sleep(0.3)
                        if process.poll() is None:
                            process.kill()

    def _gen_dh_params(self, dh_param_bits):
        exit_code = None
        cache_key = 'dh_pool_%s' % dh_param_bits
        dh_param_path = os.path.join(self.dh_pool_path,
            '%s_%s' % (dh_param_bits, uuid.uuid4().hex))
        try:
            cache_db.dict_set('dh_pool_state', dh_param_path, PENDING)
            cache_db.set_add(cache_key, dh_param_path)

            args = [
                'openssl', 'dhparam',
                '-out', dh_param_path,
                dh_param_bits,
            ]
            process = subprocess.Popen(args, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)

            listener_thread = threading.Thread(
                target=self._fill_servers_pool_listener,
                args=(cache_key, dh_param_path, process),
            )
            listener_thread.daemon = True
            listener_thread.start()

            exit_code = process.wait()
        finally:
            if exit_code == 0:
                cache_db.dict_set('dh_pool_state', dh_param_path, COMPLETE)
            else:
                cache_db.set_remove(cache_key, dh_param_path)
                cache_db.dict_remove('dh_pool_state', dh_param_path)

                try:
                    os.remove(dh_param_path)
                except:
                    pass

                logger.error('Openssl dhparam returned ' + \
                    'error exit code %r.' % exit_code)
            cache_db.publish('dh_pooler', 'poll')

    def _fill_servers_pool(self):
        end = True
        for dh_param_bits in app_server.dh_param_bits_pool:
            dh_pool_size = cache_db.set_length('dh_pool_%s' % dh_param_bits)

            if app_server.server_pool_size - dh_pool_size and not \
                    cache_db.set_length('dh_param_tasks'):
                end = False
                self._gen_dh_params(dh_param_bits)
        if not end:
            self._fill_servers_pool()

    def _fill_servers(self):
        try:
            self._fill_servers_pool()
        except:
            logger.exception('Error filling servers pool, retying...')
            time.sleep(3)
            self._fill_servers()

    def _fill_servers_thread(self):
        self._fill_servers()

        for msg in cache_db.subscribe('servers_pool'):
            if msg == 'update':
                self._fill_servers()

    def start(self):
        if self._orgs_users_thread or self._servers_thread:
            return
        self._orgs_users_thread = threading.Thread(
            target=self._fill_orgs_users_thread)
        self._orgs_users_thread.daemon = True
        self._orgs_users_thread.start()
        self._servers_thread = threading.Thread(
            target=self._fill_servers_thread)
        self._servers_thread.daemon = True
        self._servers_thread.start()
