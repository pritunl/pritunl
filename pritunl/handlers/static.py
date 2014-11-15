from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *
from pritunl import app
from pritunl import auth
from pritunl import settings
from pritunl import static
from pritunl import auth
import os
import flask

@app.app.route('/s/<path:file_path>', methods=['GET'])
@auth.session_auth
def static_get(file_path):
    try:
        static_file = static.StaticFile(settings.conf.www_path,
            file_path, cache=True)
    except InvalidStaticFile:
        return flask.abort(404)
    return static_file.get_response()

@app.app.route('/favicon.ico', methods=['GET'])
def favicon_static_get():
    static_file = static.StaticFile(settings.conf.www_path,
        'favicon.ico', cache=True)
    return static_file.get_response()

@app.app.route('/robots.txt', methods=['GET'])
def robots_static_get():
    static_file = static.StaticFile(settings.conf.www_path,
        'robots.txt', cache=True)
    return static_file.get_response()

@app.app.route('/', methods=['GET'])
def index_static_get():
    if not auth.check_session():
        return flask.redirect('login')
    static_file = static.StaticFile(settings.conf.www_path,
        'index.html', cache=False)
    return static_file.get_response()

@app.app.route('/login', methods=['GET'])
def login_static_get():
    static_file = static.StaticFile(settings.conf.www_path,
        'login.html', cache=False)
    return static_file.get_response()
