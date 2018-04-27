from pritunl.constants import *
from pritunl import settings
from pritunl import app
from pritunl import utils

import flask

@app.app.before_request
def before_request():
    if settings.local.www_state == DISABLED:
        raise flask.abort(401, settings.local.notification)

@app.app.url_value_preprocessor
def parse_object_id(_, values):
    if values:
        for key in values:
            if key.endswith('_id'):
                val = values[key]
                if len(val) > 10:
                    try:
                        values[key] = utils.ObjectIdSilent(val)
                    except:
                        values[key] = None
