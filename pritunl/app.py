from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *
from pritunl import logger
from pritunl import settings
from pritunl import patches
from pritunl import wsgiserver

import flask
import logging
import logging.handlers
import signal
import time

try:
    import OpenSSL
    from pritunl.wsgiserver import ssl_pyopenssl
    SSLAdapter = ssl_pyopenssl.pyOpenSSLAdapter
except ImportError:
    from pritunl.wsgiserver import ssl_builtin
    SSLAdapter = ssl_builtin.BuiltinSSLAdapter

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
    logger.info('Starting server', 'app')

    server = cherrypy.wsgiserver.CherryPyWSGIServer(
        (settings.conf.bind_addr, settings.conf.port), app,
        request_queue_size=settings.app.request_queue_size,
        server_name=wsgiserver.CherryPyWSGIServer.version)

    if settings.conf.ssl:
        server.ssl_adapter = SSLAdapter(
            settings.conf.server_cert_path, settings.conf.server_key_path)

    settings.local.server_ready.set()
    settings.local.server_start.wait()

    try:
        server.start()
    except (KeyboardInterrupt, SystemExit):
        pass
    except:
        logger.exception('Server error occurred', 'app')
        raise
    finally:
        _on_exit()

def _run_wsgi_debug():
    logger.info('Starting debug server', 'app')

    # App.run server uses werkzeug logger
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.setLevel(logging.DEBUG)
    werkzeug_logger.addFilter(logger.log_filter)
    werkzeug_logger.addHandler(logger.log_handler)

    settings.local.server_ready.set()
    settings.local.server_start.wait()

    try:
        app.run(host=settings.conf.bind_addr,
            port=settings.conf.port, threaded=True)
    except (KeyboardInterrupt, SystemExit):
        pass
    except:
        logger.exception('Server error occurred', 'app')
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
