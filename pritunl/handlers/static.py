from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.static_file import StaticFile
from pritunl import app_server
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
    static_file = StaticFile(app_server.www_path, file_name, cache=cache)
    return static_file.get_response()

@app_server.app.route('/s/<path:file_path>', methods=['GET'])
def static_get(file_path):
    try:
        static_file = StaticFile(app_server.www_path, file_path, cache=True)
    except InvalidStaticFile:
        return flask.abort(404)
    return static_file.get_response()
