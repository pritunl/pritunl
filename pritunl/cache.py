from pritunl.helpers import *
from pritunl import settings
from pritunl import utils

import time
import json
import redis

_set = set
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

def publish(channel, msg, cap=25, ttl=300):
    doc = json.dumps({
        'id': str(utils.ObjectId()),
        'msg': msg,
    })

    pipe = _client.pipeline()
    pipe.lpush(channel, doc)
    pipe.ltrim(channel, 0, cap)
    if ttl:
        pipe.expire(channel, ttl)
    pipe.publish(channel, doc)
    pipe.execute()

@interrupter_generator
def subscribe(channel, cursor_id=None, timeout=5):
    if timeout:
        get_timeout = 0.25
        start_time = time.time()
    else:
        get_timeout = None

    duplicates = None
    pubsub = _client.pubsub()
    pubsub.subscribe(channel)

    yield

    if cursor_id:
        found = False
        past = []
        duplicates = _set()
        history = _client.lrange(channel, 0, -1)
        for msg in history:
            doc = json.loads(msg)
            doc['id'] = utils.ObjectId(doc['id'])
            if doc['id'] == cursor_id:
                found = True
                break
            past.append(doc)
            duplicates.add(doc['id'])

            yield

        if found:
            for doc in reversed(past):
                yield doc

    yield

    while True:
        msg = pubsub.get_message(timeout=get_timeout)
        if msg and msg['type'] == 'message':
            yield

            doc = json.loads(msg['data'])
            doc['id'] = utils.ObjectId(doc['id'])
            if duplicates:
                if doc['id'] in duplicates:
                    continue
                else:
                    duplicates = None

            yield doc

        if timeout and time.time() - start_time >= timeout:
            return
