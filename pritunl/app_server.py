from pritunl.constants import *
import pritunl.patches
from pritunl import utils
from pritunl import logger
from pritunl import settings
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

class AppServer():
    def __init__(self):
        self.app = None
        self.interrupt = False
        self.conf_path = DEFAULT_CONF_PATH
        self.notification = ''
        self.www_state = OK
        self.vpn_state = OK

        self.sub_active = False
        self.sub_status = None
        self.sub_amount = None
        self.sub_period_end = None
        self.sub_cancel_at_period_end = None

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
            from pritunl import event
            if self.sub_active:
                event.Event(type=SUBSCRIPTION_ACTIVE)
            else:
                event.Event(type=SUBSCRIPTION_INACTIVE)

    def subscription_dict(self):
        return {
            'license': bool(None), # TODO
            'active': self.sub_active,
            'status': self.sub_status,
            'amount': self.sub_amount,
            'period_end': self.sub_period_end,
            'cancel_at_period_end': self.sub_cancel_at_period_end,
        }

    def _setup_app(self):
        from pritunl.app import app
        self.app = app

    def auth(self, call):
        from pritunl import auth
        def _wrapped(*args, **kwargs):
            if not auth.check_session():
                raise flask.abort(401)
            return call(*args, **kwargs)
        _wrapped.__name__ = '%s_auth' % call.__name__
        return _wrapped

    def get_temp_path(self):
        return os.path.join(settings.conf.temp_path, uuid.uuid4().hex)

    def _end_host(self):
        from pritunl import host
        host.deinit_host()

    def _setup_all(self):
        from pritunl import setup

        self._setup_app()
        setup.setup_all()

    def _run_wsgi(self):
        logger.info('Starting server...')

        server = cherrypy.wsgiserver.CherryPyWSGIServer(
            (settings.conf.bind_addr, settings.conf.port), self.app,
            request_queue_size=settings.app.request_queue_size,
            server_name=cherrypy.wsgiserver.CherryPyWSGIServer.version)
        if settings.conf.ssl:
            server.ConnectionClass = HTTPConnectionPatch
            server.ssl_adapter = SSLAdapter(
                settings.conf.server_cert_path, settings.conf.server_key_path)
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
            self.app.run(host=settings.conf.bind_addr,
                port=settings.conf.port, threaded=True)
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
        if settings.conf.debug:
            logger.LogEntry(message='Web debug server started.')
        else:
            logger.LogEntry(message='Web server started.')
        try:
            if settings.conf.debug:
                self._run_wsgi_debug()
            else:
                self._run_wsgi()
        finally:
            if settings.conf.debug:
                logger.LogEntry(message='Web debug server stopped.')
            else:
                logger.LogEntry(message='Web server stopped.')

    def run_server(self):
        self._setup_all()
        self._run_server()

app_server = AppServer()
