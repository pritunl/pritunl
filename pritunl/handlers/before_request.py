from pritunl.constants import *
import pritunl.utils as utils
from pritunl import app_server
import flask
import re

def _is_vpn_path(path):
    if re.match(r'^/server/[a-z0-9]+/tls_verify$', path) or \
            re.match(r'^/server/[a-z0-9]+/otp_verify$', path) or \
            re.match(r'^/server/[a-z0-9]+/client_connect$', path) or \
            re.match(r'^/server/[a-z0-9]+/client_disconnect$', path):
        return True
    return False

@app_server.app.before_request
def before_request():
    if app_server.www_state == DISABLED and \
            not _is_vpn_path(flask.request.path):
        raise flask.abort(401, app_server.notification)
    elif app_server.vpn_state == DISABLED and _is_vpn_path(flask.request.path):
        raise flask.abort(401, app_server.notification)
