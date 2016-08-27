from pritunl.auth.administrator import check_session

import flask

def session_auth(call):
    def _wrapped(*args, **kwargs):
        if not check_session(True):
            return flask.abort(401)
        flask.g.valid = True
        return call(*args, **kwargs)
    _wrapped.__name__ = '%s_session_auth' % call.__name__
    return _wrapped

def session_light_auth(call):
    def _wrapped(*args, **kwargs):
        if not check_session(False):
            return flask.abort(401)
        flask.g.valid = True
        return call(*args, **kwargs)
    _wrapped.__name__ = '%s_session_light_auth' % call.__name__
    return _wrapped

def open_auth(call):
    def _wrapped(*args, **kwargs):
        flask.g.valid = True
        return call(*args, **kwargs)
    _wrapped.__name__ = '%s_open_auth' % call.__name__
    return _wrapped
