from constants import *
from exceptions import *
from pritunl import app_server
from cache import cache_db, persist_db
from organization import Organization
import logging
import time
import threading

logger = logging.getLogger(APP_NAME)

class Pooler:
    def __init__(self):
        self._users_thread = None
        self._servers_thread = None

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
            pass
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
