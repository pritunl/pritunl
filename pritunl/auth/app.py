from pritunl.auth.administrator import check_session

import flask

def session_auth(call):
    def _wrapped(*args, **kwargs):
        if not check_session():
            raise flask.abort(401)
        return call(*args, **kwargs)
    _wrapped.__name__ = '%s_session_auth' % call.__name__
    return _wrapped
