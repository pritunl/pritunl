from pritunl import __version__

from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *
from pritunl import logger
from pritunl import settings
from pritunl import static
from pritunl import utils
from pritunl import upgrade
from pritunl import listener

import logging
import time
import pymongo
import flask
import threading
import subprocess
import os
import urllib.parse
import cheroot.wsgi

server = None
web_process = None
web_process_state = None
app = flask.Flask(__name__)
upgrade_done = threading.Event()
setup_ready = threading.Event()
db_ready = threading.Event()
server_ready = threading.Event()
setup_state = None

def stop_server():
    def stop():
        global web_process_state

        time.sleep(0.25)

        web_process_state = False
        try:
            web_process.kill()
        except:
            pass

    setup_ready.set()
    settings.local.server_ready.wait()
    threading.Thread(target=stop).start()

def redirect(location, code=302):
    url_root = flask.request.headers.get('PR-Forwarded-Url')

    if url_root[-1] == '/':
        url_root = url_root[:-1]

    return flask.redirect(urllib.parse.urljoin(url_root, location), code)

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

    response.headers.add('X-Frame-Options', 'DENY')

    return response

@app.route('/', methods=['GET'])
def index_get():
    if setup_state == 'upgrade':
        return redirect('upgrade')
    else:
        return redirect('setup')

@app.route('/setup', methods=['GET'])
def setup_get():
    if setup_state == 'upgrade':
        return redirect('upgrade')

    try:
        static_file = static.StaticFile(settings.conf.www_path,
            DBCONF_NAME, cache=False)
    except InvalidStaticFile:
        return flask.abort(404)

    return static_file.get_response()

@app.route('/upgrade', methods=['GET'])
def upgrade_get():
    if setup_state != 'upgrade':
        return redirect('setup')

    try:
        static_file = static.StaticFile(settings.conf.www_path,
            UPGRADE_NAME, cache=False)
    except InvalidStaticFile:
        return flask.abort(404)

    return static_file.get_response()

@app.route('/setup/s/<file_name>', methods=['GET'])
def static_get(file_name):
    file_path = {
        'fredoka-one.eot': 'fonts/fredoka-one.woff',
        'fredoka-one.woff': 'fonts/fredoka-one.woff',
        'ubuntu-bold.eot': 'fonts/ubuntu-bold.eot',
        'ubuntu-bold.woff': 'fonts/ubuntu-bold.woff',
    }[file_name]

    try:
        static_file = static.StaticFile(settings.conf.www_path,
            file_path, cache=False)
    except InvalidStaticFile:
        return flask.abort(404)

    return static_file.get_response()

@app.route('/setup/mongodb', methods=['PUT'])
def setup_mongodb_put():
    global setup_state

    setup_key = flask.request.json['setup_key']
    mongodb_uri = flask.request.json['mongodb_uri']

    if setup_state != 'setup':
        return flask.abort(404)

    if not utils.const_compare(setup_key, settings.local.setup_key):
        return utils.jsonify({
            'error': SETUP_KEY_INVALID,
            'error_msg': SETUP_KEY_INVALID_MSG,
        }, 400)

    if not mongodb_uri:
        return utils.jsonify({
            'error': MONGODB_URI_INVALID,
            'error_msg': MONGODB_URI_INVALID_MSG,
        }, 400)

    try:
        client = pymongo.MongoClient(mongodb_uri,
            connectTimeoutMS=MONGO_CONNECT_TIMEOUT)
        client.get_default_database()
    except pymongo.errors.ConfigurationError as error:
        if 'auth failed' in str(error):
            return utils.jsonify({
                'error': MONGODB_AUTH_ERROR,
                'error_msg': MONGODB_AUTH_ERROR_MSG,
            }, 400)
        raise
    except pymongo.errors.ConnectionFailure:
        return utils.jsonify({
            'error': MONGODB_CONNECT_ERROR,
            'error_msg': MONGODB_CONNECT_ERROR_MSG,
        }, 400)

    settings.conf.mongodb_uri = mongodb_uri
    settings.conf.commit()

    if check_db_ver():
        setup_state = 'upgrade'
        upgrade_database()
    else:
        stop_server()

    return ''

@app.route('/setup/upgrade', methods=['GET'])
def setup_upgrade_get():
    if upgrade_done.wait(15):
        return 'true'
    return ''

def server_thread():
    global server
    global web_process
    global web_process_state

    app.logger.setLevel(logging.DEBUG)
    app.logger.addFilter(logger.log_filter)
    app.logger.addHandler(logger.log_handler)

    server = cheroot.wsgi.Server(
        ('localhost', settings.conf.internal_port),
        app,
        shutdown_timeout=0.5,
    )
    server.server_name = ''

    if settings.conf.ssl:
        server_cert_path, server_key_path = upgrade.setup_cert()
    else:
        server_cert_path = None
        server_key_path = None

    web_process_state = True
    web_process = subprocess.Popen(
        ['pritunl-web'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=dict(os.environ, **{
            'REVERSE_PROXY_HEADER': '',
            'REVERSE_PROXY_PROTO_HEADER': '',
            'REDIRECT_SERVER': 'true',
            'BIND_HOST': settings.conf.bind_addr,
            'BIND_PORT': str(upgrade.get_server_port()),
            'INTERNAL_ADDRESS': 'localhost:%s' % settings.conf.internal_port,
            'CERT_PATH': server_cert_path or '',
            'KEY_PATH': server_key_path or '',
        }),
    )

    def poll_thread():
        time.sleep(0.5)
        if web_process.wait() and web_process_state:
            time.sleep(0.25)
            if not check_global_interrupt():
                stdout, stderr = web_process.communicate()
                logger.error(
                    'Setup web server process exited unexpectedly', 'setup',
                    stdout=stdout.decode(),
                    stderr=stderr.decode(),
                )
            set_global_interrupt()
        else:
            server.interrupt = ServerStop('Stop server')
    thread = threading.Thread(target=poll_thread)
    thread.daemon = True
    thread.start()

    try:
        server.start()
    except ServerStop:
        pass

    setup_ready.set()
    settings.local.server_start.set()

def upgrade_database():
    upgrade.database_setup()

    def _upgrade_thread():
        try:
            upgrade.upgrade_server()
            upgrade_done.set()
            stop_server()
        except:
            logger.exception('Server upgrade failed')
            set_global_interrupt()
    threading.Thread(target=_upgrade_thread).start()

def on_system_msg(msg):
    if msg['message'] == SHUT_DOWN:
        logger.warning('Received shut down event', 'setup')
        set_global_interrupt()

def check_db_ver():
    db_ver = utils.get_db_ver()
    db_min_ver = utils.get_min_db_ver()
    db_min_ver_int = utils.get_int_ver(db_min_ver)

    if settings.local.version_int < db_min_ver_int:
        logger.error('Pritunl version not compatible with database version',
            'setup',
            db_version=db_ver,
            db_min_version=db_min_ver,
            server_version=settings.local.version,
        )
        exit(75)

    return utils.get_int_ver(MIN_DATABASE_VER) > db_min_ver_int

def setup_server():
    global setup_state

    last_error = time.time() - 24
    while True:
        try:
            utils.get_db_ver_int()
            break
        except:
            time.sleep(0.5)
            if time.time() - last_error > 30:
                last_error = time.time()
                logger.exception('Error connecting to mongodb server')

    listener.add_listener('system', on_system_msg)

    if not settings.conf.mongodb_uri:
        setup_state = 'setup'
    elif check_db_ver():
        setup_state = 'upgrade'

    if setup_state:
        logger.info('Starting setup server', 'setup')

        if setup_state == 'upgrade':
            upgrade_database()

        settings.local.server_start.clear()

        thread = threading.Thread(target=server_thread)
        thread.daemon = True
        thread.start()

        setup_ready.wait()
        time.sleep(1.5)

    upgrade.database_clean_up()

    last_error = time.time() - 24
    while True:
        try:
            utils.set_db_ver(__version__, MIN_DATABASE_VER)
            break
        except:
            time.sleep(0.5)
            if time.time() - last_error > 30:
                last_error = time.time()
                logger.exception('Error connecting to mongodb server')
