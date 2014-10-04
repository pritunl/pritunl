from pritunl.auth.administrator import check_session

from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
from pritunl.settings import settings
from pritunl import logger

import flask

def session_auth(call):
    def _wrapped(*args, **kwargs):
        if not check_session():
            raise flask.abort(401)
        return call(*args, **kwargs)
    _wrapped.__name__ = '%s_session_auth' % call.__name__
    return _wrapped

def server_auth(call):
    def _wrapped(*args, **kwargs):
        api_key = flask.request.headers.get('API-Key', None)
        if api_key != settings.app.server_api_key:
            logger.error('Local auth error, invalid api key.')
            raise flask.abort(401)
        return call(*args, **kwargs)
    _wrapped.__name__ = '%s_server_auth' % call.__name__
    return _wrapped
