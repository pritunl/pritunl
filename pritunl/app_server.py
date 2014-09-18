from pritunl.constants import *
from pritunl.config import Config
from pritunl.log_filter import LogFilter
from pritunl.log_formatter import LogFormatter
import pritunl.utils as utils
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

try:
    import OpenSSL
    import cherrypy.wsgiserver.ssl_pyopenssl
    SSLAdapter = cherrypy.wsgiserver.ssl_pyopenssl.pyOpenSSLAdapter
except ImportError:
    import cherrypy.wsgiserver.ssl_builtin
    SSLAdapter = cherrypy.wsgiserver.ssl_builtin.BuiltinSSLAdapter

logger = None

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
        'get_public_ip',
        'get_notifications',
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
        'public_ip_server',
        'notification_server',
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
        'get_public_ip': True,
        'get_notifications': True,
        'ssl': True,
        'static_cache': True,
        'bind_addr': DEFAULT_BIND_ADDR,
        'port': DEFAULT_PORT,
        'pooler': True,
        'www_path': DEFAULT_WWW_PATH,
        'public_ip_server': DEFAULT_PUBLIC_IP_SERVER,
        'notification_server': DEFAULT_NOTIFICATION_SERVER,
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
            if not self.get_public_ip or self.public_ip:
                return
            if i:
                time.sleep(3)
                logger.debug('Retrying get public ip address...')
            logger.debug('Getting public ip address...')
            try:
                request = urllib2.Request(self.public_ip_server)
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
                    timeout=HTTP_REQUEST_TIMEOUT)
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
            if self.get_notifications:
                logger.debug('Checking notifications...')
                try:
                    request = urllib2.Request(self.notification_server + \
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
            time.sleep(UPDATE_CHECK_RATE)

    def _setup_public_ip(self):
        thread = threading.Thread(target=self.load_public_ip,
            kwargs={'attempts': 5})
        thread.daemon = True
        thread.start()

    def _setup_updates(self):
        thread = threading.Thread(target=self._check_updates)
        thread.daemon = True
        thread.start()

    def _setup_db(self):
        from pritunl.mongo import setup_mongo
        setup_mongo()

    def _setup_app(self):
        self.app = flask.Flask(APP_NAME)

        @self.app.before_request
        def before_request():
            flask.g.query_count = 0
            flask.g.write_count = 0
            flask.g.start = time.time()

        @self.app.after_request
        def after_request(response):
            response.headers.add('Execution-Time',
                int((time.time() - flask.g.start) * 1000))
            response.headers.add('Query-Count', flask.g.query_count)
            response.headers.add('Write-Count', flask.g.write_count)
            return response

        global logger
        logger = self.app.logger

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
        if self.log_path:
            self.log_handler = logging.handlers.RotatingFileHandler(
                self.log_path, maxBytes=1000000, backupCount=1)
        else:
            self.log_handler = logging.StreamHandler()

        global logger
        if not logger:
            logger = logging.getLogger(APP_NAME)

        self.log_filter = LogFilter()
        logger.addFilter(self.log_filter)

        logger.setLevel(logging.DEBUG)
        self.log_handler.setLevel(logging.DEBUG)

        self.log_handler.setFormatter(LogFormatter(
            '[%(asctime)s][%(levelname)s][%(module)s][%(lineno)d] ' +
            '%(message)s'))

        logger.addHandler(self.log_handler)

    def _setup_handlers(self):
        import pritunl.handlers

    def _setup_queue_runner(self):
        from pritunl.queue_runner import QueueRunner
        queue_runner = QueueRunner()
        queue_runner.start()

    def _setup_transaction_runner(self):
        from pritunl.mongo_transaction_runner import MongoTransactionRunner
        mongo_transaction_runner = MongoTransactionRunner()
        mongo_transaction_runner.start()

    def _setup_task_runner(self):
        from pritunl.task_runner import TaskRunner
        task_runner = TaskRunner()
        task_runner.start()

    def _setup_listener(self):
        import pritunl.listener as listener
        listener.start()

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
        if self.ssl:
            self._setup_server_cert()
        logger.info('Starting server...')

        server = cherrypy.wsgiserver.CherryPyWSGIServer(
            (self.bind_addr, self.port), self.app,
            request_queue_size=SERVER_REQUEST_QUEUE_SIZE,
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
        werkzeug_logger.addFilter(self.log_filter)
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
            self._on_exit()

    def _on_exit(self):
        self.interrupt = True

    def _run_server(self):
        from pritunl.log_entry import LogEntry
        LogEntry(message='Web server started.')
        try:
            if self.debug:
                self._run_wsgi_debug()
            else:
                self._run_wsgi()
        finally:
            LogEntry(message='Web server stopped.')

    def run_server(self):
        self._setup_all()
        self._run_server()
