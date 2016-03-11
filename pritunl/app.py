from pritunl import logger
from pritunl import settings
from pritunl import wsgiserver
from pritunl import limiter

import threading
import flask
import logging
import logging.handlers
import time
import os
import urlparse

try:
    import OpenSSL
    from pritunl.wsgiserver import ssl_pyopenssl
    SSLAdapter = ssl_pyopenssl.pyOpenSSLAdapter
except ImportError:
    from pritunl.wsgiserver import ssl_builtin
    SSLAdapter = ssl_builtin.BuiltinSSLAdapter

app = flask.Flask(__name__)
redirect_app = flask.Flask(__name__ + '_redirect')

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

@redirect_app.after_request
def redirect_after_request(response):
    url = list(urlparse.urlsplit(flask.request.url))
    if settings.app.ssl:
        url[0] = 'https'
    else:
        url[0] = 'http'
    if settings.conf.port != 443:
        url[1] += ':%s' % settings.app.port
    url = urlparse.urlunsplit(url)
    return flask.redirect(url)

def _run_wsgi(app_obj, ssl, port):
    logger.info('Starting server', 'app')

    server = limiter.CherryPyWSGIServerLimited(
        (settings.conf.bind_addr, port), app_obj,
        request_queue_size=settings.app.request_queue_size,
        server_name=wsgiserver.CherryPyWSGIServer.version)

    if ssl:
        server_cert_path = os.path.join(settings.conf.temp_path, 'server.crt')
        server_key_path = os.path.join(settings.conf.temp_path, 'server.key')
        server.ssl_adapter = SSLAdapter(server_cert_path, server_key_path)

    settings.local.server_ready.set()
    settings.local.server_start.wait()

    try:
        server.start()
    except (KeyboardInterrupt, SystemExit):
        pass
    except:
        logger.exception('Server error occurred', 'app')
        raise

def _run_wsgi_debug(app_obj, ssl, port):
    logger.info('Starting debug server', 'app')

    # App.run server uses werkzeug logger
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.setLevel(logging.WARNING)
    werkzeug_logger.addFilter(logger.log_filter)
    werkzeug_logger.addHandler(logger.log_handler)

    settings.local.server_ready.set()
    settings.local.server_start.wait()

    try:
        app_obj.run(host=settings.conf.bind_addr,
            port=port, threaded=True)
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
        _run_wsgi_debug(app, settings.app.ssl, settings.app.port)
    else:
        if settings.app.redirect_server:
            thread = threading.Thread(target=_run_wsgi,
                args=(redirect_app, False, 80))
            thread.daemon = True
            thread.start()
        _run_wsgi(app, settings.app.ssl, settings.app.port)
