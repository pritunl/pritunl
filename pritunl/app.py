from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *
from pritunl import logger
from pritunl import settings
from pritunl import wsgiserver
from pritunl import limiter
from pritunl import utils

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
app_server = None
redirect_app = flask.Flask(__name__ + '_redirect')
acme_token = None
acme_authorization = None
_cur_cert = None
_cur_key = None
_cur_port = None
_update_lock = threading.Lock()

def set_acme(token, authorization):
    global acme_token
    global acme_authorization
    acme_token = token
    acme_authorization = authorization

def update_server(delay=0):
    global _cur_cert
    global _cur_key
    global _cur_port

    if not settings.local.server_ready.is_set():
        return

    _update_lock.acquire()
    try:
        if _cur_cert != settings.app.server_cert or \
                _cur_key != settings.app.server_key or \
                _cur_port != settings.app.server_port:
            _cur_cert = settings.app.server_cert
            _cur_key = settings.app.server_key
            _cur_port = settings.app.server_port
            restart_server(delay=delay)
    finally:
        _update_lock.release()

def restart_server(delay=0):
    def thread_func():
        time.sleep(delay)
        set_app_server_interrupt()
        if app_server:
            app_server.interrupt = ServerRestart('Restart')
        time.sleep(1)
        clear_app_server_interrupt()
    thread = threading.Thread(target=thread_func)
    thread.daemon = True
    thread.start()

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

    if flask.request.path.startswith('/.well-known/acme-challenge/'):
        return response

    if settings.app.server_ssl:
        url[0] = 'https'
    else:
        url[0] = 'http'
    if settings.app.server_port != 443:
        url[1] += ':%s' % settings.app.server_port
    url = urlparse.urlunsplit(url)
    return flask.redirect(url)

@redirect_app.route('/.well-known/acme-challenge/<token>', methods=['GET'])
def acme_token_get(token):
    if token == acme_token:
        return flask.Response(acme_authorization, mimetype='text/plain')
    return flask.abort(404)

def _run_redirect_wsgi():
    logger.info('Starting redirect server', 'app')

    server = limiter.CherryPyWSGIServerLimited(
        (settings.conf.bind_addr, 80),
        redirect_app,
        server_name=APP_NAME,
    )

    try:
        server.start()
    except (KeyboardInterrupt, SystemExit):
        pass
    except:
        logger.exception('Redirect server error occurred', 'app')
        raise

def _run_wsgi(restart=False):
    global app_server

    logger.info('Starting server', 'app')

    app_server = limiter.CherryPyWSGIServerLimited(
        (settings.conf.bind_addr, settings.app.server_port),
        app,
        request_queue_size=settings.app.request_queue_size,
        server_name=APP_NAME,
    )
    app_server.shutdown_timeout = 1

    if settings.app.server_ssl:
        utils.write_server_cert()

        server_cert_path = os.path.join(settings.conf.temp_path,
            SERVER_CERT_NAME)
        server_key_path = os.path.join(settings.conf.temp_path,
            SERVER_KEY_NAME)
        app_server.ssl_adapter = SSLAdapter(
            server_cert_path,
            server_key_path,
        )

    if not restart:
        settings.local.server_ready.set()
        settings.local.server_start.wait()

    try:
        app_server.start()
    except (KeyboardInterrupt, SystemExit):
        pass
    except ServerRestart:
        logger.info('Server restarting...', 'app')
        return _run_wsgi(True)
    except:
        logger.exception('Server error occurred', 'app')
        raise

def _run_wsgi_debug():
    logger.info('Starting debug server', 'app')

    # App.run server uses werkzeug logger
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.setLevel(logging.WARNING)
    werkzeug_logger.addFilter(logger.log_filter)
    werkzeug_logger.addHandler(logger.log_handler)

    settings.local.server_ready.set()
    settings.local.server_start.wait()

    try:
        app.run(
            host=settings.conf.bind_addr,
            port=settings.app.server_port,
            threaded=True,
        )
    except (KeyboardInterrupt, SystemExit):
        pass
    except:
        logger.exception('Server error occurred', 'app')
        raise

def run_server():
    global _cur_cert
    global _cur_key
    global _cur_port
    _cur_cert = settings.app.server_cert
    _cur_key = settings.app.server_key
    _cur_port = settings.app.server_port

    if settings.conf.debug:
        logger.LogEntry(message='Web debug server started.')
    else:
        logger.LogEntry(message='Web server started.')

    if settings.conf.debug:
        _run_wsgi_debug()
    else:
        if settings.app.redirect_server:
            thread = threading.Thread(target=_run_redirect_wsgi)
            thread.daemon = True
            thread.start()
        _run_wsgi()
