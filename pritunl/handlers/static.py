from pritunl.exceptions import *
from pritunl.constants import *
from pritunl import app
from pritunl import settings
from pritunl import static
from pritunl import auth
from pritunl import utils

import flask

@app.app.route('/s/', methods=['GET'])
@app.app.route('/s/<path:file_path>', methods=['GET'])
@auth.session_light_auth
def static_get(file_path=None):
    if settings.conf.debug and 'styles/fonts/' in file_path:
        file_path = file_path.replace('styles/fonts/', 'fonts/', 1)

    if not file_path:
        return flask.abort(404)

    try:
        static_file = static.StaticFile(settings.conf.www_path,
            file_path, cache=True)
    except InvalidStaticFile:
        return flask.abort(404)

    return static_file.get_response()

@app.app.route('/fredoka-one.eot', methods=['GET'])
@auth.open_auth
def fredoka_eot_static_get():
    static_file = static.StaticFile(settings.conf.www_path,
        'fonts/fredoka-one.eot', cache=True)
    return static_file.get_response()

@app.app.route('/ubuntu-bold.eot', methods=['GET'])
@auth.open_auth
def ubuntu_eot_static_get():
    static_file = static.StaticFile(settings.conf.www_path,
        'fonts/ubuntu-bold.eot', cache=True)
    return static_file.get_response()

@app.app.route('/fredoka-one.woff', methods=['GET'])
@auth.open_auth
def fredoka_woff_static_get():
    static_file = static.StaticFile(settings.conf.www_path,
        'fonts/fredoka-one.woff', cache=True)
    return static_file.get_response()

@app.app.route('/ubuntu-bold.woff', methods=['GET'])
@auth.open_auth
def ubuntu_woff_static_get():
    static_file = static.StaticFile(settings.conf.www_path,
        'fonts/ubuntu-bold.woff', cache=True)
    return static_file.get_response()

@app.app.route('/favicon.ico', methods=['GET'])
@auth.open_auth
def favicon_static_get():
    static_file = static.StaticFile(settings.conf.www_path,
        'favicon.ico', cache=True)
    return static_file.get_response()

@app.app.route('/robots.txt', methods=['GET'])
@auth.open_auth
def robots_static_get():
    static_file = static.StaticFile(settings.conf.www_path,
        'robots.txt', cache=True)
    return static_file.get_response()

@app.app.route('/', methods=['GET'])
@auth.open_auth
def index_static_get():
    if not auth.check_session(False):
        return utils.redirect('login')

    static_file = static.StaticFile(settings.conf.www_path,
        'index.html', cache=False)

    return static_file.get_response()

@app.app.route('/login', methods=['GET'])
@auth.open_auth
def login_static_get():
    if auth.check_session(False):
        return utils.redirect('')

    static_file = static.StaticFile(settings.conf.www_path,
        'login.html', cache=False, gzip=False)

    bodyClass = ''

    if settings.local.sub_active:
        if settings.app.theme == 'dark':
            bodyClass += 'dark '

        if settings.local.sub_plan == 'enterprise':
            if not settings.app.sso:
                pass
            elif settings.app.sso in (SAML_AUTH, SAML_DUO_AUTH):
                bodyClass += 'sso-saml '
            elif SAML_OKTA_AUTH in settings.app.sso:
                bodyClass += 'sso-okta '
            elif SAML_ONELOGIN_AUTH in settings.app.sso:
                bodyClass += 'sso-onelogin '
            elif GOOGLE_AUTH in settings.app.sso:
                bodyClass += 'sso-google '
            elif SLACK_AUTH in settings.app.sso:
                bodyClass += 'sso-slack '
            elif settings.app.sso == DUO_AUTH:
                bodyClass += 'sso-duo '

            if settings.app.sso and DUO_AUTH in settings.app.sso:
                bodyClass += 'sso-duo-auth '

    if settings.app.demo_mode:
        bodyClass += 'demo '

    static_file.data = static_file.data.replace(
        '<body>', '<body class="' + bodyClass + '">')

    return static_file.get_response()
