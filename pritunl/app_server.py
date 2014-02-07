from constants import *
from cache import cache_db, persist_db
from config import Config
import utils
import flask
import cherrypy.wsgiserver
import cherrypy.wsgiserver.ssl_builtin
import os
import logging
import signal
import time
import json
import urllib2
import threading
import hashlib
import subprocess
import base64

logger = None

class AppServer(Config):
    bool_options = {'debug', 'log_debug', 'auto_start_servers',
        'get_public_ip', 'inline_certs', 'ssl'}
    int_options = {'port', 'session_timeout', 'key_bits', 'dh_param_bits'}
    path_options = {'log_path', 'db_path', 'www_path', 'data_path',
        'server_cert_path', 'server_key_path'}
    str_options = {'bind_addr', 'username', 'password', 'public_ip_server'}
    default_options = {
        'auto_start_servers': True,
        'get_public_ip': True,
        'inline_certs': True,
        'ssl': True,
        'username': DEFAULT_USERNAME,
        'session_timeout': DEFAULT_SESSION_TIMEOUT,
        'key_bits': DEFAULT_KEY_BITS,
        'dh_param_bits': DEFAULT_DH_PARAM_BITS,
        'db_path': DEFAULT_DB_PATH,
        'www_path': DEFAULT_WWW_PATH,
        'data_path': DEFAULT_DATA_PATH,
        'public_ip_server': DEFAULT_PUBLIC_IP_SERVER,
    }

    def __init__(self):
        Config.__init__(self)
        self.app = None
        self.interrupt = False

    def __getattr__(self, name):
        if name == 'web_protocol':
            if not self.ssl:
                return 'http'
            return 'https'
        elif name == 'password_data':
            if self.password[:2] == '1$':
                pass_split = self.password.split('$')
                return (1, pass_split[1], pass_split[2])
            else:
                return (0, PASSWORD_SALT_V0, self.password)
        elif name == 'ssl':
            if self.debug:
                return False
        return Config.__getattr__(self, name)

    def load_public_ip(self, retry=False, timeout=3):
        if not self.get_public_ip:
            return
        logger.debug('Getting public ip address...')
        try:
            request = urllib2.Request(self.public_ip_server)
            response = urllib2.urlopen(request, timeout=timeout)
            self.public_ip = json.load(response)['ip']
        except:
            if retry:
                logger.debug('Retrying get public ip address...')
                time.sleep(5)
                self.load_public_ip(timeout=timeout)
            else:
                logger.exception('Failed to get public ip address...')

    def _setup_public_ip(self):
        self.public_ip = None
        threading.Thread(target=self.load_public_ip,
            kwargs={'retry': True, 'timeout': 10}).start()

    def _setup_app(self):
        self.app = flask.Flask(APP_NAME)
        self.app.secret_key = os.urandom(32)

        @self.app.before_request
        def before_request():
            flask.g.start = time.time()

        @self.app.after_request
        def after_request(response):
            response.headers.add('Execution-Time',
                int((time.time() - flask.g.start) * 1000))
            return response

        global logger
        logger = self.app.logger

    def auth(self, call):
        def _wrapped(*args, **kwargs):
            if not utils.check_auth():
                raise flask.abort(401)
            return call(*args, **kwargs)
        _wrapped.__name__ = '%s_auth' % call.__name__
        return _wrapped

    def local_only(self, call):
        def _wrapped(*args, **kwargs):
            if utils.get_remote_addr() not in ('127.0.0.1', '::1'):
                raise flask.abort(401)
            return call(*args, **kwargs)
        _wrapped.__name__ = '%s_local_only' % call.__name__
        return _wrapped

    def _setup_conf(self):
        self.set_path(self.conf_path)
        if not os.path.isdir(self.data_path):
            os.makedirs(self.data_path)

    def _setup_log(self):
        if self.log_debug:
            self.log_level = logging.DEBUG
        else:
            self.log_level = logging.INFO

        if self.log_path:
            self.log_handler = logging.FileHandler(self.log_path)
        else:
            self.log_handler = logging.StreamHandler()

        global logger
        if not logger:
            logger = logging.getLogger(APP_NAME)

        logger.setLevel(self.log_level)
        self.log_handler.setLevel(self.log_level)

        self.log_handler.setFormatter(logging.Formatter(
            '[%(asctime)s][%(levelname)s][%(module)s][%(lineno)d] ' +
            '%(message)s'))

        logger.addHandler(self.log_handler)

    def _setup_db(self):
        persist_db.setup_persist(self.db_path)

    def _setup_handlers(self):
        import handlers

    def _setup_static_handler(self):
        from werkzeug import SharedDataMiddleware

        self.app.wsgi_app = SharedDataMiddleware(self.app.wsgi_app, {
            '/': os.path.normpath(self.www_path),
        }, cache=False)

        @self.app.route('/', methods=['GET'])
        def index_get():
            with open(os.path.join(self.www_path, 'index.html'), 'r') as fd:
                return fd.read()

    def _get_version_int(self, version):
        return int(''.join([x.zfill(2) for x in version.split('.')]))

    def _get_version(self):
        from pritunl import __version__
        return self._get_version_int(__version__)

    def _get_data_version(self):
        version_path = os.path.join(self.data_path, VERSION_NAME)
        if os.path.isfile(version_path):
            with open(version_path, 'r') as version_file:
                return self._get_version_int(
                    version_file.readlines()[0].strip())

    def _upgrade_db(self):
        version = self._get_version()
        cur_version = self._get_data_version()

        if cur_version and cur_version < self._get_version_int('0.10.5'):
            logger.info('Upgrading database to v0.10.5...')
            try:
                os.remove(self.db_path)
            except OSError:
                pass

    def _upgrade_data(self):
        version = self._get_version()
        cur_version = self._get_data_version()

        if cur_version and cur_version < self._get_version_int('0.10.4'):
            logger.info('Upgrading data to v0.10.4...')
            from organization import Organization
            for org in Organization.iter_orgs():
                for user in org.iter_users():
                    user._upgrade_0_10_4()

        if cur_version and cur_version < self._get_version_int('0.10.5'):
            logger.info('Upgrading data to v0.10.5...')
            from server import Server
            for server in Server.iter_servers():
                server._upgrade_0_10_5()

            from organization import Organization
            for org in Organization.iter_orgs():
                org._upgrade_0_10_5()

        if cur_version != version:
            from pritunl import __version__
            version_path = os.path.join(self.data_path, VERSION_NAME)
            with open(version_path, 'w') as version_file:
                version_file.write('%s\n' % __version__)

    def _fill_cache(self):
        logger.info('Preloading cache...')
        from organization import Organization
        for org in Organization.iter_orgs():
            org._cache_users()

    def _hash_password_v0(self, salt, password):
        password_hash = hashlib.sha512()
        password_hash.update(password[:PASSWORD_LEN_LIMIT])
        password_hash.update(salt)
        return password_hash.hexdigest()

    def _hash_password_v1(self, salt, password):
        pass_hash = hashlib.sha512()
        pass_hash.update(password[:PASSWORD_LEN_LIMIT])
        pass_hash.update(base64.b64decode(salt))
        hash_digest = pass_hash.digest()

        for i in xrange(5):
            pass_hash = hashlib.sha512()
            pass_hash.update(hash_digest)
            hash_digest = pass_hash.digest()
        return base64.b64encode(hash_digest)

    def check_account(self, username, password, remote_addr=None):
        if remote_addr:
            cache_key = 'ip_' + remote_addr
            count = cache_db.list_length(cache_key)
            if count and count > 10:
                raise flask.abort(403)

            key_exists = cache_db.exists(cache_key)
            cache_db.list_rpush(cache_key, '')
            if not key_exists:
                cache_db.expire(cache_key, 20)

        if username != self.username:
            return False

        if not self.password:
            if password == DEFAULT_PASSWORD:
                return True
            return False

        pass_ver, pass_salt, pass_hash = self.password_data
        if pass_ver == 0:
            return self._hash_password_v0(
                pass_salt, password) == pass_hash
        elif pass_ver == 1:
            return self._hash_password_v1(
                pass_salt, password) == pass_hash
        return False

    def set_password(self, password):
        salt = base64.b64encode(os.urandom(8))
        pass_hash = self._hash_password_v1(salt, password)
        self.password = '1$%s$%s' % (salt, pass_hash)
        self.commit()

    def _setup_all(self):
        self._setup_app()
        self._setup_conf()
        self._setup_log()
        self._setup_public_ip()
        self._upgrade_db()
        self._setup_db()
        self._setup_handlers()
        self._setup_static_handler()
        self._upgrade_data()
        self._fill_cache()

    def _setup_server_cert(self):
        if self.server_cert_path and self.server_key_path:
            self._server_cert_path = self.server_cert_path
            self._server_key_path = self.server_key_path
        else:
            self._server_cert_path = os.path.join(self.data_path,
                SERVER_CERT_NAME)
            self._server_key_path = os.path.join(self.data_path,
                SERVER_KEY_NAME)

            if not os.path.isfile(self._server_cert_path) or \
                    not os.path.isfile(self._server_key_path):
                logger.info('Generating server ssl cert...')
                try:
                    subprocess.check_call([
                        'openssl', 'req', '-batch', '-x509', '-nodes',
                        '-newkey', 'rsa:4096',
                        '-days', '3652',
                        '-keyout', self._server_key_path,
                        '-out', self._server_cert_path,
                    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                except subprocess.CalledProcessError:
                    logger.exception('Failed to generate server ssl cert.')
                    raise
                os.chmod(self._server_key_path, 0600)

    def _run_wsgi(self):
        if self.ssl:
            self._setup_server_cert()
        from log_entry import LogEntry
        logger.info('Starting server...')

        if self.auto_start_servers:
            from pritunl.server import Server
            for server in Server.iter_servers():
                if server.org_count:
                    try:
                        server.start()
                    except:
                        logger.exception('Failed to auto start server. %r' % {
                            'server_id': server.id,
                        })

        server = cherrypy.wsgiserver.CherryPyWSGIServer(
            (self.bind_addr, self.port), self.app,
            request_queue_size=SERVER_REQUEST_QUEUE_SIZE,
            server_name=cherrypy.wsgiserver.CherryPyWSGIServer.version)
        if self.ssl:
            server.ssl_adapter = \
                cherrypy.wsgiserver.ssl_builtin.BuiltinSSLAdapter(
                    self._server_cert_path, self._server_key_path)
        try:
            server.start()
        except (KeyboardInterrupt, SystemExit):
            pass
        except:
            logger.exception('Server error occurred')
            raise
        finally:
            signal.signal(signal.SIGINT, signal.SIG_IGN)
            logger.info('Stopping server...')
            LogEntry(message='Web server stopped.')
            self.interrupt = True
            server.stop()

    def _run_wsgi_debug(self):
        from log_entry import LogEntry
        logger.info('Starting debug server...')

        # App.run server uses werkzeug logger
        werkzeug_logger = logging.getLogger('werkzeug')
        werkzeug_logger.setLevel(self.log_level)
        werkzeug_logger.addHandler(self.log_handler)

        try:
            self.app.run(host=self.bind_addr, port=self.port, threaded=True)
        except (KeyboardInterrupt, SystemExit):
            pass
        except:
            logger.exception('Server error occurred')
            raise
        finally:
            signal.signal(signal.SIGINT, signal.SIG_IGN)
            logger.info('Stopping debug server...')
            LogEntry(message='Web server stopped.')
            self.interrupt = True

    def _run_server(self):
        from log_entry import LogEntry
        LogEntry(message='Web server started.')
        if self.debug:
            self._run_wsgi_debug()
        else:
            self._run_wsgi()

    def run_server(self):
        self._setup_all()
        self._run_server()
