from pritunl.exceptions import *
from pritunl.constants import *
from pritunl.helpers import *
from pritunl import logger
from pritunl import journal
from pritunl import settings
from pritunl import utils
from pritunl import monitoring
from pritunl import auth
from pritunl import acme

import threading
import flask
import time
import subprocess
import os
import cheroot.wsgi

app = flask.Flask(__name__)
app_server = None
_cur_ssl = None
_cur_cert = None
_cur_key = None
_cur_port = None
_cur_redirect_server = None
_cur_reverse_proxy = None
_update_lock = threading.Lock()
_watch_event = threading.Event()

def update_server(delay=0):
    global _cur_ssl
    global _cur_cert
    global _cur_key
    global _cur_port
    global _cur_redirect_server
    global _cur_reverse_proxy

    if not settings.local.server_ready.is_set():
        return

    _update_lock.acquire()
    if settings.local.web_state == DISABLED:
        logger.warning(
            'Web server disabled',
            'server',
            message=settings.local.notification,
        )
        stop_server()
        return

    try:
        if _cur_ssl != settings.app.server_ssl or \
                _cur_cert != settings.app.server_cert or \
                _cur_key != settings.app.server_key or \
                _cur_port != settings.app.server_port or \
                _cur_redirect_server != settings.app.redirect_server or \
                _cur_reverse_proxy != (settings.app.reverse_proxy_header if
                    settings.app.reverse_proxy else ''):
            logger.info('Settings changed, restarting server...', 'app',
                ssl_changed=_cur_ssl != settings.app.server_ssl,
                cert_changed=_cur_cert != settings.app.server_cert,
                key_changed=_cur_key != settings.app.server_key,
                port_changed=_cur_port != settings.app.server_port,
                redirect_server_changed=_cur_redirect_server !=
                    settings.app.redirect_server,
                reverse_proxy_changed= _cur_reverse_proxy != (
                    settings.app.reverse_proxy_header if
                    settings.app.reverse_proxy else ''),
            )

            _cur_ssl = settings.app.server_ssl
            _cur_cert = settings.app.server_cert
            _cur_key = settings.app.server_key
            _cur_port = settings.app.server_port
            _cur_redirect_server = settings.app.redirect_server
            _cur_reverse_proxy = settings.app.reverse_proxy_header if \
                settings.app.reverse_proxy else ''

            if settings.app.server_auto_restart:
                restart_server(delay=delay)
    finally:
        _update_lock.release()

def stop_server(delay=0):
    _watch_event.clear()
    def thread_func():
        time.sleep(delay)
        set_app_server_interrupt()
        if app_server:
            app_server.interrupt = ServerStop('Stop')
        time.sleep(1)
        clear_app_server_interrupt()
    thread = threading.Thread(target=thread_func)
    thread.daemon = True
    thread.start()

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

def restart_server_fast():
    _watch_event.clear()
    set_app_server_interrupt()
    if app_server:
        app_server.interrupt = ServerRestart('Restart')
    time.sleep(1)
    clear_app_server_interrupt()

@app.before_request
def before_request():
    flask.g.valid = False
    flask.g.start = time.time()

@app.after_request
def after_request(response):
    if settings.app.check_requests and not flask.g.valid:
        raise ValueError('Request not authorized')

    response.headers.add('X-Frame-Options', 'DENY')

    if settings.app.server_ssl or settings.app.reverse_proxy:
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
    token = utils.filter_str(token[:96])
    authorization = acme.get_authorization(token)
    if authorization:
        return flask.Response(authorization, mimetype='text/plain')
    return flask.abort(404)

def _run_server(restart):
    global app_server

    try:
        context = subprocess.check_output(
            ['id', '-Z'],
            stderr=subprocess.PIPE,
        ).decode().strip()
    except:
        context = 'none'

    journal.entry(
        journal.WEB_SERVER_START,
        selinux_context=context,
    )

    logger.info('Starting server', 'app',
        selinux_context=context,
    )

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

    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SECURE=True,
    )

    if settings.app.server_ssl:
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
        env=dict(os.environ, **{
            'REVERSE_PROXY_HEADER': settings.app.reverse_proxy_header if \
                settings.app.reverse_proxy else '',
            'REVERSE_PROXY_PROTO_HEADER': \
                settings.app.reverse_proxy_proto_header if \
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
                logger.error('Web server process exited unexpectedly', 'app')
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
    except ServerStop:
        return
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
            if settings.local.web_state == DISABLED:
                time.sleep(1)
                continue
            _run_server(restart)
        except ServerRestart:
            restart = True
            logger.info('Server restarting...', 'app')

def setup_server_cert():
    global _cur_cert
    global _cur_key

    if not settings.app.server_cert or not settings.app.server_key:
        logger.info('Generating server certificate...', 'app')
        utils.create_server_cert()
        settings.commit()

        _cur_cert = settings.app.server_cert
        _cur_key = settings.app.server_key

def run_server():
    global _cur_ssl
    global _cur_cert
    global _cur_key
    global _cur_port
    global _cur_redirect_server
    global _cur_reverse_proxy
    _cur_ssl = settings.app.server_ssl
    _cur_cert = settings.app.server_cert
    _cur_key = settings.app.server_key
    _cur_port = settings.app.server_port
    _cur_redirect_server = settings.app.redirect_server
    _cur_reverse_proxy = settings.app.reverse_proxy_header if \
        settings.app.reverse_proxy else ''

    logger.LogEntry(message='Web server started.')

    _run_wsgi()
