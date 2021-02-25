from pritunl.helpers import *
from pritunl import settings
from pritunl import utils
from pritunl import logger

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

    logger.info('Connecting to Redis', 'cache',
        redis_uri=redis_uri,
    )

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

def publish(channels, message, extra=None, cap=50, ttl=300):
    if isinstance(channels, str):
        channels = [channels]

    for channel in channels:
        doc = {
            '_id': utils.ObjectId(),
            'message': message,
            'timestamp': utils.now(),
        }
        if extra:
            for key, val in list(extra.items()):
                doc[key] = val

        doc = json.dumps(doc, default=utils.json_default)

        pipe = _client.pipeline()
        pipe.lpush(channel, doc)
        pipe.ltrim(channel, 0, cap)
        if ttl:
            pipe.expire(channel, ttl)
        pipe.publish(channel, doc)
        pipe.execute()

def get_cursor_id(channel):
    msg = _client.lindex(channel, 0)
    if msg:
        doc = json.loads(msg, object_hook=utils.json_object_hook_handler)
        return doc['_id']

@interrupter_generator
def subscribe(channels, cursor_id=None, timeout=None, yield_delay=None,
        yield_app_server=False):
    if timeout:
        get_timeout = 0.5
        start_time = time.time()
    else:
        get_timeout = None

    duplicates = None
    yield_stop = False
    pubsub = _client.pubsub()

    try:
        if isinstance(channels, str):
            channels = [channels]

        for channel in channels:
            pubsub.subscribe(channel)

        yield

        if cursor_id:
            if len(channels) > 1:
                raise TypeError(
                    'Cannot specify cursor_id with multiple channels')

            found = False
            past = []
            duplicates = _set()
            history = _client.lrange(channels[0], 0, -1)
            for msg in history:
                doc = json.loads(
                    msg,
                    object_hook=utils.json_object_hook_handler,
                )
                if doc['_id'] == cursor_id:
                    found = True
                    break
                doc['channel'] = channels[0]
                past.append(doc)
                duplicates.add(doc['_id'])

                yield

            if found:
                for doc in reversed(past):
                    yield doc

        yield

        while True:
            msg = pubsub.get_message(timeout=get_timeout)
            if msg and msg['type'] == 'message':
                yield

                doc = json.loads(msg['data'],
                    object_hook=utils.json_object_hook_handler)
                doc['channel'] = msg['channel']
                if duplicates:
                    if doc['_id'] in duplicates:
                        continue
                    else:
                        duplicates = None

                yield doc

                if yield_stop:
                    return

                if yield_delay:
                    get_timeout = yield_delay
                    yield_stop = True
                    continue

            if yield_stop or (yield_app_server and
                    check_app_server_interrupt()) or (timeout and
                    time.time() - start_time >= timeout):
                return
    finally:
        pubsub.close()
