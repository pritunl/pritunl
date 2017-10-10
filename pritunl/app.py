from pritunl.exceptions import *
from pritunl.helpers import *
from pritunl import logger
from pritunl import settings
from pritunl import utils
from pritunl import monitoring
from pritunl import auth

import threading
import flask
import logging
import logging.handlers
import time
import subprocess
import os
import cheroot.wsgi

app = flask.Flask(__name__)
app_server = None
acme_token = None
acme_authorization = None
_cur_ssl = None
_cur_cert = None
_cur_key = None
_cur_port = None
_cur_reverse_proxy = None
_update_lock = threading.Lock()
_watch_event = threading.Event()

def set_acme(token, authorization):
    global acme_token
    global acme_authorization
    acme_token = token
    acme_authorization = authorization

def update_server(delay=0):
    global _cur_ssl
    global _cur_cert
    global _cur_key
    global _cur_port
    global _cur_reverse_proxy

    if not settings.local.server_ready.is_set():
        return

    _update_lock.acquire()
    try:
        if _cur_ssl != settings.app.server_ssl or \
                _cur_cert != settings.app.server_cert or \
                _cur_key != settings.app.server_key or \
                _cur_port != settings.app.server_port or \
                _cur_reverse_proxy != (settings.app.reverse_proxy_header if
                    settings.app.reverse_proxy else ''):
            logger.info('Settings changed, restarting server...', 'app',
                ssl_changed=_cur_ssl != settings.app.server_ssl,
                cert_changed=_cur_cert != settings.app.server_cert,
                key_changed=_cur_key != settings.app.server_key,
                port_changed=_cur_port != settings.app.server_port,
                reverse_proxy_changed= _cur_reverse_proxy != (
                    settings.app.reverse_proxy_header if
                    settings.app.reverse_proxy else ''),
            )

            _cur_ssl = settings.app.server_ssl
            _cur_cert = settings.app.server_cert
            _cur_key = settings.app.server_key
            _cur_port = settings.app.server_port
            _cur_reverse_proxy = settings.app.reverse_proxy_header if \
                settings.app.reverse_proxy else ''

            if settings.app.server_auto_restart:
                restart_server(delay=delay)
    finally:
        _update_lock.release()

def restart_server(delay=0):
    _watch_event.clear()
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
    flask.g.valid = False
    flask.g.start = time.time()

@app.after_request
def after_request(response):
    if settings.app.check_requests and not flask.g.valid:
        raise ValueError('Request not authorized')

    response.headers.add('X-Frame-Options', 'DENY')

    if settings.app.server_ssl:
        response.headers.add('Strict-Transport-Security', 'max-age=31536000')

    if not flask.request.path.startswith('/event'):
        monitoring.insert_point('requests', {
            'host': settings.local.host.name,
        }, {
            'path': flask.request.path,
            'remote_ip': utils.get_remote_addr(),
            'response_time': int((time.time() - flask.g.start) * 1000),
        })

    return response

@app.route('/.well-known/acme-challenge/<token>', methods=['GET'])
@auth.open_auth
def acme_token_get(token):
    if token == acme_token:
        return flask.Response(acme_authorization, mimetype='text/plain')
    return flask.abort(404)

def _run_server(restart):
    global app_server

    logger.info('Starting server', 'app')

    app_server = cheroot.wsgi.Server(
        ('localhost', settings.app.server_internal_port),
        app,
        request_queue_size=settings.app.request_queue_size,
        accepted_queue_size=settings.app.request_accepted_queue_size,
        numthreads=settings.app.request_thread_count,
        max=settings.app.request_max_thread_count,
        shutdown_timeout=3,
    )
    app_server.server_name = ''

    server_cert_path = None
    server_key_path = None
    redirect_server = 'true' if settings.app.redirect_server else 'false'
    internal_addr = 'localhost:%s' % settings.app.server_internal_port

    if settings.app.server_ssl:
        app.config.update(
            SESSION_COOKIE_SECURE=True,
        )

        setup_server_cert()

        server_cert_path, server_key_path = utils.write_server_cert(
            settings.app.server_cert,
            settings.app.server_key,
            settings.app.acme_domain,
        )

    if not restart:
        settings.local.server_ready.set()
        settings.local.server_start.wait()

    process_state = True
    process = subprocess.Popen(
        ['pritunl-web'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=dict(os.environ, **{
            'REVERSE_PROXY_HEADER': settings.app.reverse_proxy_header if \
                settings.app.reverse_proxy else '',
            'REDIRECT_SERVER': redirect_server,
            'BIND_HOST': settings.conf.bind_addr,
            'BIND_PORT': str(settings.app.server_port),
            'INTERNAL_ADDRESS': internal_addr,
            'CERT_PATH': server_cert_path or '',
            'KEY_PATH': server_key_path or '',
        }),
    )

    def poll_thread():
        time.sleep(0.5)
        if process.wait() and process_state:
            time.sleep(0.25)
            if not check_global_interrupt():
                stdout, stderr = process._communicate(None)
                logger.error('Web server process exited unexpectedly', 'app',
                    stdout=stdout,
                    stderr=stderr,
                )
                time.sleep(1)
                restart_server(1)
    thread = threading.Thread(target=poll_thread)
    thread.daemon = True
    thread.start()

    _watch_event.set()

    try:
        app_server.start()
    except (KeyboardInterrupt, SystemExit):
        return
    except ServerRestart:
        raise
    except:
        logger.exception('Server error occurred', 'app')
        raise
    finally:
        process_state = False
        try:
            process.kill()
        except:
            pass

def _run_wsgi():
    restart = False
    while True:
        try:
            _run_server(restart)
        except ServerRestart:
            restart = True
            logger.info('Server restarting...', 'app')

def setup_server_cert():
    if not settings.app.server_cert or not settings.app.server_key:
        logger.info('Generating server certificate...', 'app')
        utils.create_server_cert()
        settings.commit()

def run_server():
    global _cur_ssl
    global _cur_cert
    global _cur_key
    global _cur_port
    global _cur_reverse_proxy
    _cur_ssl = settings.app.server_ssl
    _cur_cert = settings.app.server_cert
    _cur_key = settings.app.server_key
    _cur_port = settings.app.server_port
    _cur_reverse_proxy = settings.app.reverse_proxy_header if \
        settings.app.reverse_proxy else ''

    logger.LogEntry(message='Web server started.')

    _run_wsgi()
