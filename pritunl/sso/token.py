from pritunl.constants import *
from pritunl.exceptions import *
from pritunl import listener
from pritunl import utils

_tokens = {}

def _on_msg(msg):
    if msg['message'] != 'authorized':
        return
    token = msg.get('token')
    user_id = msg.get('user_id')

    if not token or not user_id:
        return

    _tokens[token] = {
        'user_id': user_id,
        'timestamp': utils.now()
    }

def check_token(token, user_id):
    data = _tokens.get(token)
    if not data or user_id != data['user_id']:
        return False
    return True

def init_token():
    listener.add_listener('tokens', _on_msg)
