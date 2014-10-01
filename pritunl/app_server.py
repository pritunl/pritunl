from pritunl.constants import *
import pritunl.patches
from pritunl.config import Config
from pritunl import utils
from pritunl import logger
from pritunl.settings import settings
import flask
import cherrypy.wsgiserver
import os
import logging
import logging.handlers
import signal
import time
import json
import urllib2
import threading
import subprocess
import uuid
import hashlib

try:
    import OpenSSL
    import cherrypy.wsgiserver.ssl_pyopenssl
    SSLAdapter = cherrypy.wsgiserver.ssl_pyopenssl.pyOpenSSLAdapter
except ImportError:
    import cherrypy.wsgiserver.ssl_builtin
    SSLAdapter = cherrypy.wsgiserver.ssl_builtin.BuiltinSSLAdapter

class HTTPConnectionPatch(cherrypy.wsgiserver.HTTPConnection):
    def __init__(self, server, sock,
            makefile=cherrypy.wsgiserver.CP_fileobject):
        self.server = server
        self.socket = sock
        self.rfile = makefile(sock, 'rb', self.rbufsize)
        self.wfile = makefile(sock, 'wb', self.wbufsize)
        self.requests_seen = 0

class AppServer(Config):
    bool_options = {
        'debug',
        'ssl',
        'static_cache',
    }
    int_options = {
        'port',
    }
    path_options = {
        'log_path',
        'www_path',
        'server_cert_path',
        'server_key_path',
    }
    str_options = {
        'bind_addr',
        'mongodb_url',
        'mongodb_collection_prefix',
    }
    ignore_options = {
        'log_debug',
        'auto_start_servers',
        'inline_certs',
        'pooler',
        'session_timeout',
        'key_bits',
        'dh_param_bits',
        'org_pool_size',
        'user_pool_size',
        'server_user_pool_size',
        'server_pool_size',
        'server_log_lines',
        'db_path',
        'data_path',
        'password',
        'dh_param_bits_pool',
    }
    default_options = {
        'ssl': True,
        'static_cache': True,
        'bind_addr': DEFAULT_BIND_ADDR,
        'port': DEFAULT_PORT,
        'pooler': True,
        'www_path': DEFAULT_WWW_PATH,
    }
    read_env = True

    def __init__(self):
        Config.__init__(self)
        self.app = None
        self.interrupt = False
        self.public_ip = None
        self.conf_path = DEFAULT_CONF_PATH
        self.notification = ''
        self.www_state = OK
        self.vpn_state = OK
        self.sub_active = False
        self.sub_status = None
        self.sub_amount = None
        self.sub_period_end = None
        self.sub_cancel_at_period_end = None
        self.pooler_instance = None
        self.openssl_heartbleed = not utils.check_openssl()
        self.server_api_key = None
        self.host_id = hashlib.sha1(str(uuid.getnode())).hexdigest()

    def __getattr__(self, name):
        if name == 'web_protocol':
            if not self.ssl:
                return 'http'
            return 'https'
        elif name == 'ssl':
            if self.debug:
                return False
        return Config.__getattr__(self, name)

    def load_public_ip(self, attempts=1, timeout=5):
        for i in xrange(attempts):
            if self.public_ip:
                return
            if i:
                time.sleep(3)
                logger.debug('Retrying get public ip address...')
            logger.debug('Getting public ip address...')
            try:
                request = urllib2.Request(
                    settings.app.public_ip_server)
                response = urllib2.urlopen(request, timeout=timeout)
                self.public_ip = json.load(response)['ip']
                break
            except:
                pass
        if not self.public_ip:
            logger.exception('Failed to get public ip address...')

    def subscription_update(self):
        cur_sub_active = self.sub_active
        license = None # TODO
        if not license:
            self.sub_active = False
            self.sub_status = None
            self.sub_amount = None
            self.sub_period_end = None
            self.sub_cancel_at_period_end = None
        else:
            try:
                response = utils.request.get(SUBSCRIPTION_SERVER,
                    json_data={'license': license},
                    timeout=max(settings.app.http_request_timeout, 10))
                # License key invalid
                if response.status_code == 470:
                    #persist_db.remove('license')
                    self.subscription_update()
                    return
                data = response.json()
            except:
                logger.exception('Failed to check subscription status...')
                data = {}
            self.sub_active = data.get('active', True)
            self.sub_status = data.get('status', 'unknown')
            self.sub_amount = data.get('amount')
            self.sub_period_end = data.get('period_end')
            self.sub_cancel_at_period_end = data.get('cancel_at_period_end')
        if cur_sub_active is not None and cur_sub_active != self.sub_active:
            from pritunl.event import Event
            if self.sub_active:
                Event(type=SUBSCRIPTION_ACTIVE)
            else:
                Event(type=SUBSCRIPTION_INACTIVE)

    def subscription_dict(self):
        return {
            'license': bool(None), # TODO
            'active': self.sub_active,
            'status': self.sub_status,
            'amount': self.sub_amount,
            'period_end': self.sub_period_end,
            'cancel_at_period_end': self.sub_cancel_at_period_end,
        }

    def _check_updates(self):
        while True:
            if not settings.app.update_check_rate:
                time.sleep(60)
                continue

            logger.debug('Checking notifications...')
            try:
                request = urllib2.Request(
                    settings.app.notification_server +
                    '/%s' % self._get_version())
                response = urllib2.urlopen(request, timeout=60)
                data = json.load(response)

                self.notification = data.get('message', '')
                self.www_state = data.get('www', OK)
                self.vpn_state = data.get('vpn', OK)
            except:
                logger.exception('Failed to check notifications.')

            logger.debug('Checking subscription status...')
            try:
                self.subscription_update()
            except:
                logger.exception('Failed to check subscription status.')
            time.sleep(settings.app.update_check_rate)

    def _setup_public_ip(self):
        self.load_public_ip()
        if not self.public_ip:
            thread = threading.Thread(target=self.load_public_ip,
                kwargs={'attempts': 5})
            thread.daemon = True
            thread.start()

    def _setup_updates(self):
        thread = threading.Thread(target=self._check_updates)
        thread.daemon = True
        thread.start()

    def _setup_db(self):
        from pritunl import setup
        setup.setup_mongo()

    def _setup_app(self):
        self.app = flask.Flask(APP_NAME)

        @self.app.before_request
        def before_request():
            flask.g.query_count = 0
            flask.g.write_count = 0
            flask.g.query_time = 0
            flask.g.start = time.time()

        @self.app.after_request
        def after_request(response):
            response.headers.add('Execution-Time',
                int((time.time() - flask.g.start) * 1000))
            response.headers.add('Query-Time',
                int(flask.g.query_time * 1000))
            response.headers.add('Query-Count', flask.g.query_count)
            response.headers.add('Write-Count', flask.g.write_count)
            return response

    def auth(self, call):
        from administrator import Administrator
        def _wrapped(*args, **kwargs):
            if not Administrator.check_session():
                raise flask.abort(401)
            return call(*args, **kwargs)
        _wrapped.__name__ = '%s_auth' % call.__name__
        return _wrapped

    def server_auth(self, call):
        def _wrapped(*args, **kwargs):
            api_key = flask.request.headers.get('API-Key', None)
            if api_key != self.server_api_key:
                logger.error('Local auth error, invalid api key.')
                raise flask.abort(401)
            return call(*args, **kwargs)
        _wrapped.__name__ = '%s_server_auth' % call.__name__
        return _wrapped

    def get_temp_path(self):
        temp_path = os.path.join(self.temp_path, uuid.uuid4().hex)
        return temp_path

    def _setup_conf(self):
        self.set_path(self.conf_path)

    def _setup_temp_path(self):
        # TODO
        self.temp_path = 'tmp/pritunl'
        if not os.path.isdir(self.temp_path):
            os.makedirs(self.temp_path)

    def _setup_log(self):
        logger.setup_logger()
        self.app.logger.setLevel(logging.DEBUG)
        self.app.logger.addFilter(logger.log_filter)
        self.app.logger.addHandler(logger.log_handler)

    def _setup_handlers(self):
        import pritunl.handlers

    def _setup_queue_runner(self):
        from pritunl import queue
        queue.start_runner()

    def _setup_transaction_runner(self):
        from pritunl import transaction
        transaction.start_runner()

    def _setup_task_runner(self):
        from pritunl.task.runner import TaskRunner
        task_runner = TaskRunner()
        task_runner.start()

    def _setup_listener(self):
        import pritunl.listener as listener
        listener.start()

    def _setup_host(self):
        from pritunl import host
        hst = host.init_host()
        hst.keep_alive()

    def _end_host(self):
        from pritunl import host
        host.deinit_host()

    def _get_version_int(self, version):
        return int(''.join([x.zfill(2) for x in version.split('.')]))

    def _get_version(self):
        from pritunl import __version__
        return self._get_version_int(__version__)

    def _setup_all(self):
        self._setup_app()
        self._setup_conf()
        self._setup_db()
        self._setup_temp_path()
        self._setup_log()
        self._setup_public_ip()
        self._setup_updates()
        self._setup_handlers()
        self._setup_queue_runner()
        self._setup_transaction_runner()
        self._setup_task_runner()
        self._setup_listener()
        self._setup_host()

    def _setup_server_cert(self):
        if not os.path.isfile(self.server_cert_path) or \
                not os.path.isfile(self.server_key_path):
            logger.info('Generating server ssl cert...')
            try:
                subprocess.check_call([
                    'openssl', 'req', '-batch', '-x509', '-nodes', '-sha256',
                    '-newkey', 'rsa:4096',
                    '-days', '3652',
                    '-keyout', self.server_key_path,
                    '-out', self.server_cert_path,
                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except subprocess.CalledProcessError:
                logger.exception('Failed to generate server ssl cert.')
                raise
            os.chmod(self.server_key_path, 0600)

    def _run_wsgi(self):
        from pritunl.settings import settings

        if self.ssl:
            self._setup_server_cert()
        logger.info('Starting server...')

        server = cherrypy.wsgiserver.CherryPyWSGIServer(
            (self.bind_addr, self.port), self.app,
            request_queue_size=settings.app.request_queue_size,
            server_name=cherrypy.wsgiserver.CherryPyWSGIServer.version)
        if self.ssl:
            server.ConnectionClass = HTTPConnectionPatch
            server.ssl_adapter = SSLAdapter(
                self.server_cert_path, self.server_key_path)
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
            self._on_exit()

    def _run_wsgi_debug(self):
        logger.info('Starting debug server...')

        # App.run server uses werkzeug logger
        werkzeug_logger = logging.getLogger('werkzeug')
        werkzeug_logger.setLevel(logging.DEBUG)
        werkzeug_logger.addFilter(logger.log_filter)
        werkzeug_logger.addHandler(logger.log_handler)

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
            self._on_exit()

    def _on_exit(self):
        self._end_host()
        self.interrupt = True

    def _run_server(self):
        if self.debug:
            logger.LogEntry(message='Web debug server started.')
        else:
            logger.LogEntry(message='Web server started.')
        try:
            if self.debug:
                self._run_wsgi_debug()
            else:
                self._run_wsgi()
        finally:
            if self.debug:
                logger.LogEntry(message='Web debug server stopped.')
            else:
                logger.LogEntry(message='Web server stopped.')

    def run_server(self):
        self._setup_all()
        self._run_server()

app_server = AppServer()
