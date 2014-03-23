from pritunl.constants import *
import pritunl.utils as utils
from pritunl import app_server
import flask

@app_server.app.before_request
def before_request():
    if app_server.www_state == DISABLED:
        raise flask.abort(401, app_server.notification)
