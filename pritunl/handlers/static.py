from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *
from pritunl import app
from pritunl import settings
from pritunl import static
from pritunl import auth
import os
import flask

@app.app.route('/', methods=['GET'])
@app.app.route('/favicon.ico', methods=['GET'])
@app.app.route('/robots.txt', methods=['GET'])
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

@app.app.route('/s/<path:file_path>', methods=['GET'])
def static_get(file_path):
    try:
        static_file = static.StaticFile(settings.conf.www_path,
            file_path, cache=True)
    except InvalidStaticFile:
        return flask.abort(404)
    return static_file.get_response()
