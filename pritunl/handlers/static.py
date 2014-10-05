from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.app_server import app_server
from pritunl import settings
from pritunl import static
import os
import flask

@app_server.app.route('/', methods=['GET'])
@app_server.app.route('/favicon.ico', methods=['GET'])
@app_server.app.route('/robots.txt', methods=['GET'])
def root_static_get():
    file_name = flask.request.path.lstrip('/')
    if not file_name:
        file_name = 'index.html'
        cache = False
    else:
        cache = True
    static_file = static.StaticFile(settings.conf.www_path,
        file_name, cache=cache)
    return static_file.get_response()

@app_server.app.route('/s/<path:file_path>', methods=['GET'])
def static_get(file_path):
    try:
        static_file = static.StaticFile(settings.conf.www_path,
            file_path, cache=True)
    except InvalidStaticFile:
        return flask.abort(404)
    return static_file.get_response()
