from pritunl.constants import *
from pritunl.exceptions import *
from pritunl import listener
from pritunl import utils
from pritunl import settings

import threading

_tokens = {}
_tokens_lock = threading.Lock()
_last_clean = utils.time_now()

def _on_msg(msg):
    if msg['message'] != 'authorized':
        return
    token = msg.get('token')
    user_id = msg.get('user_id')
    server_id = msg.get('server_id')

    if not token or not user_id or not server_id:
        return

    with _tokens_lock:
        if utils.time_now() - _last_clean > settings.vpn.sso_token_ttl:
            clean_tokens()

        _tokens[token] = {
            'user_id': user_id,
            'server_id': server_id,
            'timestamp': utils.time_now()
        }

def check_token(token, user_id, server_id):
    data = _tokens.get(token)
    if not data or user_id != data['user_id'] or \
            server_id != data['server_id']:
        return False
    if utils.time_now() - data[
            'timestamp'] > settings.vpn.sso_token_ttl:
        return False
    return True

def clean_tokens():
    cur_time = utils.time_now()
    _last_clean = cur_time
    ttl = settings.vpn.sso_token_ttl * 2
    for token in list(_tokens.keys()):
        data = _tokens.get(token)
        if data and cur_time - data['timestamp'] > ttl:
            del _tokens[token]

def init_token():
    listener.add_listener('tokens', _on_msg)
