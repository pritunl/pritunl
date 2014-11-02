from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *
from pritunl import logger
from pritunl import settings
from pritunl import static
from pritunl import utils

import cherrypy.wsgiserver
import logging
import logging.handlers
import signal
import time
import os
import pymongo
import json
import flask

server = None
app = flask.Flask(APP_NAME + '_dbconf')

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

@app.route('/', methods=['GET'])
def index_get():
    return flask.redirect('setup')

@app.route('/setup', methods=['GET'])
def setup_get():
    return utils.response(open(os.path.join(
        settings.conf.www_path, 'dbconf_index.html')))

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

@app.route('/mongodb', methods=['PUT'])
def mongodb_put():
    return utils.jsonify({
        'test': 'test',
    })

def _run_wsgi():
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

def _run_wsgi_debug():
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
        _run_wsgi_debug()
    else:
        _run_wsgi()
