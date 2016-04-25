from pritunl.helpers import *
from pritunl.constants import *
from pritunl import settings

import redis

_client = None
has_cache = False

def init():
    global _client
    global has_cache

    redis_uri = settings.app.redis_uri
    if not redis_uri:
        return

    has_cache = True
    _client = redis.StrictRedis.from_url(
        redis_uri,
        socket_timeout=3,
        socket_connect_timeout=3,
    )

def get(key):
    return _client.get(key)

def set(key, val):
    return _client.set(key, val)

def remove(key):
    return  _client.delete(key)
