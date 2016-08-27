from pritunl import settings

import base64
import hashlib
import hmac
import flask

def get_sig(sig_str, secret):
    return base64.b64encode(
        hmac.new(secret, sig_str, hashlib.sha512).digest(),
    )

def get_flask_sig():
    sig_str = '&'.join((
        flask.session['session_id'],
        flask.session['admin_id'],
        str(flask.session['timestamp']),
    ))
    return get_sig(
        settings.app.cookie_secret2,
        sig_str,
    )

def set_flask_sig():
    flask.session['signature'] = get_flask_sig()

def check_flask_sig():
    return flask.session.get('signature') == get_flask_sig()
