from pritunl import settings
from pritunl import utils

import json
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
        socket_timeout=settings.app.redis_timeout,
        socket_connect_timeout=settings.app.redis_timeout,
    )

def get(key):
    return _client.get(key)

def set(key, val, ttl=None):
    if ttl:
        _client.setex(key, ttl, val)
    else:
        _client.set(key, val)

def lpush(key, *vals, **kwargs):
    ttl = kwargs.get('ttl')
    cap = kwargs.get('cap')

    if not ttl and not cap:
        _client.lpush(key, *vals)
    else:
        pipe = _client.pipeline()
        pipe.lpush(key, *vals)
        if cap:
            pipe.ltrim(key, 0, cap)
        if ttl:
            pipe.expire(key, ttl)
        pipe.execute()

def rpush(key, *vals, **kwargs):
    ttl = kwargs.get('ttl')
    cap = kwargs.get('cap')

    if not ttl and not cap:
        _client.rpush(key, *vals)
    else:
        pipe = _client.pipeline()
        pipe.rpush(key, *vals)
        if cap:
            pipe.ltrim(key, 0, cap)
        if ttl:
            pipe.expire(key, ttl)
        pipe.execute()

def remove(key):
    return  _client.delete(key)

def publish(channel, msg, cap=25):
    doc = json.dumps({
        'id': str(utils.ObjectId()),
        'msg': msg,
    })

    pipe = _client.pipeline()
    pipe.lpush(channel, doc)
    pipe.ltrim(channel, 0, cap)
    pipe.publish(channel, doc)
    pipe.execute()
