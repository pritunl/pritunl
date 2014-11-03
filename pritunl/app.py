from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *
from pritunl import logger
from pritunl import settings

import flask
import cherrypy.wsgiserver
import logging
import logging.handlers
import signal
import time

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

app = flask.Flask(APP_NAME)

@app.before_request
def before_request():
    flask.g.query_count = 0
    flask.g.write_count = 0
    flask.g.query_time = 0
    flask.g.start = time.time()

@app.after_request
def after_request(response):
    response.headers.add('Execution-Time',
        int((time.time() - flask.g.start) * 1000))
    response.headers.add('Query-Time',
        int(flask.g.query_time * 1000))
    response.headers.add('Query-Count', flask.g.query_count)
    response.headers.add('Write-Count', flask.g.write_count)
    return response

def _run_wsgi():
    logger.info('Starting server...')

    server = cherrypy.wsgiserver.CherryPyWSGIServer(
        (settings.conf.bind_addr, settings.conf.port), app,
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
        _on_exit()

def _run_wsgi_debug():
    logger.info('Starting debug server...')

    # App.run server uses werkzeug logger
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.setLevel(logging.DEBUG)
    werkzeug_logger.addFilter(logger.log_filter)
    werkzeug_logger.addHandler(logger.log_handler)

    try:
        app.run(host=settings.conf.bind_addr,
            port=settings.conf.port, threaded=True)
    except (KeyboardInterrupt, SystemExit):
        pass
    except:
        logger.exception('Server error occurred')
        raise

def run_server():
    if settings.conf.debug:
        logger.LogEntry(message='Web debug server started.')
    else:
        logger.LogEntry(message='Web server started.')

    if settings.conf.debug:
        _run_wsgi_debug()
    else:
        _run_wsgi()
