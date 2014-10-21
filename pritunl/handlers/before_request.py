from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *
from pritunl import utils
from pritunl import settings
from pritunl import app
from pritunl import auth

import flask
import re
import bson

def _is_vpn_path(path):
    if re.match(r'^/server/[a-z0-9]+/tls_verify$', path) or \
            re.match(r'^/server/[a-z0-9]+/otp_verify$', path) or \
            re.match(r'^/server/[a-z0-9]+/client_connect$', path) or \
            re.match(r'^/server/[a-z0-9]+/client_disconnect$', path):
        return True
    return False

@app.app.before_request
def before_request():
    if settings.local.www_state == DISABLED and \
            not _is_vpn_path(flask.request.path):
        raise flask.abort(401, settings.local.notification)
    elif settings.local.vpn_state == DISABLED and _is_vpn_path(
            flask.request.path):
        raise flask.abort(401, settings.local.notification)

@app.app.url_value_preprocessor
def parse_object_id(endpoint, values):
    for key in values:
        if key.endswith('_id'):
            values[key] = bson.ObjectId(values[key])
