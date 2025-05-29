from pritunl.constants import *
from pritunl.exceptions import *
from pritunl import listener
from pritunl import utils
from pritunl import settings
from pritunl import mongo

import threading
import datetime

_tokens = {}
_tokens_lock = threading.Lock()

def _on_msg(msg):
    if msg['message'] != 'authorized':
        return
    token = msg.get('token')
    user_id = msg.get('user_id')
    server_id = msg.get('server_id')

    if not token or not user_id or not server_id:
        return

    with _tokens_lock:
        _tokens[token] = {
            'user_id': user_id,
            'server_id': server_id,
            'timestamp': utils.now()
        }

def sync_tokens():
    tokens_collection = mongo.get_collection('server_sso_tokens')
    new_tokens = {}

    for doc in tokens_collection.find({}):
        token = doc.get('_id')
        user_id = doc.get('user_id')
        server_id = doc.get('server_id')
        if not token or not user_id or not server_id:
            continue

        new_tokens[token] = {
            'user_id': user_id,
            'server_id': server_id,
            'timestamp': utils.now()
        }

    with _tokens_lock:
        global _tokens
        _tokens = new_tokens

def check_token(token, user_id, server_id):
    token_ttl = datetime.timedelta(seconds=settings.vpn.sso_token_ttl)
    with _tokens_lock:
        data = _tokens.get(token)
    if not data or user_id != data['user_id'] or \
            server_id != data['server_id']:
        return False
    if utils.now() - data['timestamp'] > token_ttl:
        return False
    return True

def init_token():
    listener.add_listener('tokens', _on_msg)
