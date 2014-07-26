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

logger = logging.getLogger(APP_NAME)

class Pooler:
    def __init__(self):
        self._users_thread = None
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

            cache_db.set_add('dh_pool_%s' % dh_param_bits, dh_param_path)

    def _fill_users(self):
        try:
            for org in Organization.iter_orgs():
                for _ in xrange(
                        app_server.user_pool_size - org.client_pool_count):
                    org.new_user(type=CERT_CLIENT_POOL)
                for _ in xrange(
                        app_server.server_pool_size - org.server_pool_size):
                    org.new_user(type=CERT_SERVER_POOL)
        except:
            # Exception can occur when org is deleted whiling filling
            logger.exception('Error filling users pool, retying...')
            time.sleep(3)
            self._fill_users()

    def _fill_users_thread(self):
        self._fill_users()

        for msg in cache_db.subscribe('users_pool'):
            if msg == 'update':
                self._fill_users()

    def _fill_servers(self):
        try:
            for dh_param_bits in app_server.dh_param_bits_pool:
                dh_pool_size = cache_db.set_length(
                    'dh_pool_%s' % dh_param_bits)

                for _ in xrange(app_server.server_pool_size - dh_pool_size):
                    dh_param_path = os.path.join(self.dh_pool_path,
                        '%s_%s' % (dh_param_bits, uuid.uuid4().hex))
                    try:
                        args = [
                            'openssl', 'dhparam',
                            '-out', dh_param_path,
                            dh_param_bits,
                        ]
                        subprocess.check_call(args, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
                    except:
                        try:
                            os.remove(dh_param_path)
                        except:
                            pass
                        raise

                    cache_db.set_add(
                        'dh_pool_%s' % dh_param_bits, dh_param_path)
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
        if self._users_thread or self._servers_thread:
            return
        self._users_thread = threading.Thread(
            target=self._fill_users_thread)
        self._users_thread.daemon = True
        self._users_thread.start()
        self._servers_thread = threading.Thread(
            target=self._fill_servers_thread)
        self._servers_thread.daemon = True
        self._servers_thread.start()
