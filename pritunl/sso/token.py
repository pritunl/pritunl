from pritunl.constants import *
from pritunl.exceptions import *
from pritunl import listener
from pritunl import utils
from pritunl import settings

_tokens = {}

def _on_msg(msg):
    if msg['message'] != 'authorized':
        return
    token = msg.get('token')
    user_id = msg.get('user_id')
    server_id = msg.get('server_id')

    if not token or not user_id or not server_id:
        return

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

def init_token():
    listener.add_listener('tokens', _on_msg)
