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

@app.app.route('/logo.png', methods=['GET'])
@auth.open_auth
def logo_static_get():
    static_file = static.StaticFile(settings.conf.www_path,
        'logo.png', cache=True)
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

    body_class = ''

    if auth.has_default_password():
        body_class += 'default-pass '

    if settings.local.sub_active:
        if settings.app.theme == 'dark':
            body_class += 'dark '

        if settings.local.sub_plan and \
                'enterprise' in settings.local.sub_plan:
            if not settings.app.sso:
                pass
            elif settings.app.sso in (SAML_AUTH, SAML_DUO_AUTH):
                body_class += 'sso-saml '
            elif SAML_OKTA_AUTH in settings.app.sso:
                body_class += 'sso-okta '
            elif SAML_ONELOGIN_AUTH in settings.app.sso:
                body_class += 'sso-onelogin '
            elif AZURE_AUTH in settings.app.sso:
                body_class += 'sso-azure '
            elif GOOGLE_AUTH in settings.app.sso:
                body_class += 'sso-google '
            elif AUTHZERO_AUTH in settings.app.sso:
                body_class += 'sso-authzero '
            elif SLACK_AUTH in settings.app.sso:
                body_class += 'sso-slack '
            elif settings.app.sso == DUO_AUTH:
                body_class += 'sso-duo '

            if settings.app.sso and DUO_AUTH in settings.app.sso and \
                    settings.app.sso != DUO_AUTH and \
                    settings.app.sso_duo_mode != 'passcode':
                body_class += 'sso-duo-auth '

    if settings.app.demo_mode:
        body_class += 'demo '

    static_file.data = static_file.data.replace(
        '<body>', '<body class="' + body_class + '">')

    return static_file.get_response()

@app.app.route('/setup', methods=['GET'])
@auth.open_auth
def setup_get():
    return utils.redirect('')

@app.app.route('/upgrade', methods=['GET'])
@auth.open_auth
def upgrade_get():
    return utils.redirect('')
