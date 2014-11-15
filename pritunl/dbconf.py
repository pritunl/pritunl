from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *
from pritunl import logger
from pritunl import settings
from pritunl import static
from pritunl import utils
from pritunl import patches
from pritunl import wsgiserver

import logging
import signal
import time
import os
import pymongo
import json
import flask
import threading

server = None
app = flask.Flask(APP_NAME + '_dbconf')
dbconf_ready = threading.Event()

def stop_server():
    server.interrupt = StopServer('Stop server')

try:
    import OpenSSL
    import wsgiserver.ssl_pyopenssl
    SSLAdapter = wsgiserver.ssl_pyopenssl.pyOpenSSLAdapter
except ImportError:
    import wsgiserver.ssl_builtin
    SSLAdapter = wsgiserver.ssl_builtin.BuiltinSSLAdapter

@app.route('/', methods=['GET'])
def index_get():
    return flask.redirect('setup')

@app.route('/setup', methods=['GET'])
def setup_get():
    try:
        static_file = static.StaticFile(settings.conf.www_path,
            DBCONF_NAME, cache=False)
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
def mongodb_put():
    mongodb_uri = flask.request.json['mongodb_uri']

    if not mongodb_uri:
        return utils.jsonify({
            'error': MONGODB_URI_INVALID,
            'error_msg': MONGODB_URI_INVALID_MSG,
        }, 400)

    try:
        client = pymongo.MongoClient(mongodb_uri,
            connectTimeoutMS=MONGO_CONNECT_TIMEOUT)
    except pymongo.errors.ConnectionFailure:
        return utils.jsonify({
            'error': MONGODB_CONNECT_ERROR,
            'error_msg': MONGODB_CONNECT_ERROR_MSG,
        }, 400)

    settings.conf.mongodb_uri = mongodb_uri
    settings.conf.commit()

    dbconf_ready.set()
    settings.local.server_ready.wait()
    threading.Thread(target=stop_server).start()

    return ''

def server_thread():
    app.logger.setLevel(logging.DEBUG)
    app.logger.addFilter(logger.log_filter)
    app.logger.addHandler(logger.log_handler)

    global server
    server = wsgiserver.CherryPyWSGIServer(
        (settings.conf.bind_addr, settings.conf.port), app,
        server_name=wsgiserver.CherryPyWSGIServer.version,
        timeout=1,
        shutdown_timeout=0.5,
    )

    if settings.conf.ssl:
        server.ConnectionClass = patches.HTTPConnectionPatch
        server.ssl_adapter = SSLAdapter(
            settings.conf.server_cert_path, settings.conf.server_key_path)

    try:
        server.start()
    except StopServer:
        pass

    dbconf_ready.set()
    settings.local.server_start.set()

def run_server():
    settings.local.server_start.clear()

    thread = threading.Thread(target=server_thread)
    thread.daemon = True
    thread.start()

    dbconf_ready.wait()
