from pritunl.utils.filter import session_str
from pritunl.utils.misc import const_compare
from pritunl import settings

import base64
import hashlib
import hmac
import flask

def get_sig(sig_str, secret):
    return base64.b64encode(
        hmac.new(secret.encode(), sig_str.encode(), hashlib.sha512).digest(),
    ).decode()

def get_flask_sig():
    sig_str = '&'.join((
        session_str('session_id'),
        session_str('admin_id'),
        session_str('timestamp'),
    ))
    return get_sig(
        settings.app.cookie_secret2,
        sig_str,
    )

def set_flask_sig():
    flask.session['signature'] = get_flask_sig()

def check_flask_sig():
    return const_compare(session_str('signature'), get_flask_sig())
