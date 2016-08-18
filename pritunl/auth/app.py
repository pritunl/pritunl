from pritunl.auth.administrator import check_session, check_session_csrf

import flask

def session_auth(call):
    def _wrapped(*args, **kwargs):
        if not check_session_csrf():
            return flask.abort(401)
        flask.g.authed = True
        return call(*args, **kwargs)
    _wrapped.__name__ = '%s_session_auth' % call.__name__
    return _wrapped

def session_light_auth(call):
    def _wrapped(*args, **kwargs):
        if not check_session():
            return flask.abort(401)
        flask.g.authed = True
        return call(*args, **kwargs)
    _wrapped.__name__ = '%s_session_auth' % call.__name__
    return _wrapped

def open_auth(call):
    def _wrapped(*args, **kwargs):
        flask.g.authed = True
        return call(*args, **kwargs)
    _wrapped.__name__ = '%s_open_auth' % call.__name__
    return _wrapped
