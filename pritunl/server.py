import os
import logging
import signal
import time
from constants import *
from config import Config

logger = None

class Server(Config):
    bool_options = ['debug', 'log_debug']
    int_options = ['port']
    path_options = ['log_path', 'www_path']
    str_options = ['bind_addr']

    def __init__(self):
        Config.__init__(self)
        self.app = None
        self.interrupt = False

    def _setup_app(self):
        import flask
        self.app = flask.Flask(APP_NAME)

        global logger
        logger = self.app.logger

    def _setup_conf(self):
        self.set_path(self.conf_path)

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

    def _setup_handlers(self):
        import handlers

    def _setup_static_handler(self):
        www_path = self.www_path or DEFAULT_WWW_PATH

        from werkzeug import SharedDataMiddleware

        self.app.wsgi_app = SharedDataMiddleware(self.app.wsgi_app, {
            '/': os.path.normpath(www_path),
        }, cache=False)

        @self.app.route('/', methods=['GET'])
        def index_get():
            with open(os.path.join(www_path, 'index.html'), 'r') as fd:
                return fd.read()

    def _setup_all(self):
        self._setup_app()
        self._setup_conf()
        self._setup_log()
        self._setup_handlers()
        self._setup_static_handler()

    def _run_wsgi(self):
        import cherrypy.wsgiserver

        logger.info('Starting server...')

        server = cherrypy.wsgiserver.CherryPyWSGIServer(
            (self.bind_addr, self.port), self.app)
        try:
            server.start()
        except (KeyboardInterrupt, SystemExit), exc:
            signal.signal(signal.SIGINT, signal.SIG_IGN)
            self.interrupt = True
            logger.info('Stopping server...')
            server.stop()

    def _run_wsgi_debug(self):
        logger.info('Starting debug server...')

        # App.run server uses werkzeug logger
        werkzeug_logger = logging.getLogger('werkzeug')
        werkzeug_logger.setLevel(self.log_level)
        werkzeug_logger.addHandler(self.log_handler)

        try:
            self.app.run(host=self.bind_addr, port=self.port, threaded=True)
        finally:
            signal.signal(signal.SIGINT, signal.SIG_IGN)
            self.interrupt = True
            logger.info('Stopping server...')

    def _run_server(self):
        if self.debug:
            self._run_wsgi_debug()
        else:
            self._run_wsgi()

    def run_server(self):
        self._setup_all()
        self._run_server()

    def run_all(self):
        self._setup_all()
        self._run_server()
