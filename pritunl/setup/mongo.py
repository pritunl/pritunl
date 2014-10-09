from pritunl import app
from pritunl import settings
from pritunl import logger
from pritunl import mongo
from pritunl import auth

import pymongo
import bson
import re
import os
import base64
import flask
import random
import time

def setup_mongo():
    if not pymongo.has_c():
        logger.warning('Failed to load pymongo c bindings')

    if not bson.has_c():
        logger.warning('Failed to load bson c bindings')

    prefix = settings.conf.mongodb_collection_prefix or ''
    last_error = time.time() - 24
    while True:
        try:
            client = pymongo.MongoClient(settings.conf.mongodb_url,
                connectTimeoutMS=2000)
            break
        except pymongo.errors.ConnectionFailure:
            time.sleep(0.5)
            if time.time() - last_error > 30:
                last_error = time.time()
                logger.exception('Error connecting to mongodb server')

    database = client.get_default_database()
    cur_collections = database.collection_names()

    if prefix + 'messages' not in cur_collections:
        database.create_collection(prefix + 'messages', capped=True,
            size=100000)

    mongo.collections.update({
        'transaction': getattr(database, prefix + 'transaction'),
        'queue': getattr(database, prefix + 'queue'),
        'task': getattr(database, prefix + 'task'),
        'system': getattr(database, prefix + 'system'),
        'messages': getattr(database, prefix + 'messages'),
        'administrators': getattr(database, prefix + 'administrators'),
        'users': getattr(database, prefix + 'users'),
        'organizations': getattr(database, prefix + 'organizations'),
        'hosts': getattr(database, prefix + 'hosts'),
        'hosts_usage': getattr(database, prefix + 'hosts_usage'),
        'servers': getattr(database, prefix + 'servers'),
        'servers_output': getattr(database, prefix + 'servers_output'),
        'servers_bandwidth': getattr(database, prefix + 'servers_bandwidth'),
        'servers_ip_pool': getattr(database, prefix + 'servers_ip_pool'),
        'dh_params': getattr(database, prefix + 'dh_params'),
        'auth_nonces': getattr(database, prefix + 'auth_nonces'),
        'auth_limiter': getattr(database, prefix + 'auth_limiter'),
        'otp': getattr(database, prefix + 'otp'),
        'otp_cache': getattr(database, prefix + 'otp_cache'),
    })

    if prefix + 'log_entries' not in cur_collections:
        log_limit = settings.app.log_entry_limit
        database.create_collection(prefix + 'log_entries', capped=True,
            size=log_limit * 256 * 2, max=log_limit)

    mongo.collections.update({
        'log_entries': getattr(database, prefix + 'log_entries'),
    })

    for collection_name, collection in mongo.collections.items():
        collection.name_str = collection_name

    settings.init()

    mongo.collections['transaction'].ensure_index('lock_id', unique=True)
    mongo.collections['transaction'].ensure_index([
        ('ttl_timestamp', pymongo.ASCENDING),
        ('state', pymongo.ASCENDING),
        ('priority', pymongo.DESCENDING),
    ])
    mongo.collections['queue'].ensure_index('runner_id')
    mongo.collections['queue'].ensure_index('ttl_timestamp')
    mongo.collections['task'].ensure_index('type', unique=True)
    mongo.collections['task'].ensure_index('ttl_timestamp')
    mongo.collections['log_entries'].ensure_index([
        ('timestamp', pymongo.DESCENDING),
    ])
    mongo.collections['messages'].ensure_index('channel')
    mongo.collections['administrators'].ensure_index('username', unique=True)
    mongo.collections['users'].ensure_index([
        ('type', pymongo.ASCENDING),
        ('org_id', pymongo.ASCENDING),
    ])
    mongo.collections['users'].ensure_index([
        ('org_id', pymongo.ASCENDING),
        ('name', pymongo.ASCENDING),
    ])
    mongo.collections['organizations'].ensure_index('type')
    mongo.collections['hosts'].ensure_index('name')
    mongo.collections['hosts_usage'].ensure_index([
        ('host_id', pymongo.ASCENDING),
        ('timestamp', pymongo.ASCENDING),
    ])
    mongo.collections['servers'].ensure_index('name')
    mongo.collections['servers'].ensure_index('ping_timestamp')
    mongo.collections['servers_output'].ensure_index([
        ('server_id', pymongo.ASCENDING),
        ('timestamp', pymongo.ASCENDING),
    ])
    mongo.collections['servers_bandwidth'].ensure_index([
        ('server_id', pymongo.ASCENDING),
        ('period', pymongo.ASCENDING),
        ('timestamp', pymongo.ASCENDING),
    ])
    mongo.collections['servers_ip_pool'].ensure_index([
        ('server_id', pymongo.ASCENDING),
        ('user_id', pymongo.ASCENDING),
    ])
    mongo.collections['servers_ip_pool'].ensure_index('user_id')
    mongo.collections['dh_params'].ensure_index('dh_param_bits')
    mongo.collections['auth_nonces'].ensure_index([
        ('token', pymongo.ASCENDING),
        ('nonce', pymongo.ASCENDING),
    ], unique=True)
    mongo.collections['auth_nonces'].ensure_index('timestamp',
        expireAfterSeconds=settings.app.auth_time_window * 2.1)
    mongo.collections['auth_limiter'].ensure_index('timestamp',
        expireAfterSeconds=settings.app.auth_limiter_ttl)
    mongo.collections['otp'].ensure_index('timestamp',
        expireAfterSeconds=120)
    mongo.collections['otp_cache'].ensure_index('timestamp',
        expireAfterSeconds=settings.user.otp_cache_ttl)

    if not auth.Administrator.collection.find_one():
        auth.Administrator(
            username=DEFAULT_USERNAME,
            password=DEFAULT_PASSWORD,
            default=True,
        ).commit()

    secret_key = settings.app.cookie_secret
    if not secret_key:
        secret_key = re.sub(r'[\W_]+', '',
            base64.b64encode(os.urandom(128)))[:64]
        settings.app.cookie_secret = secret_key
        settings.commit()
    app.app.secret_key = secret_key.encode()

    server_api_key = settings.app.server_api_key
    if not server_api_key:
        server_api_key = re.sub(r'[\W_]+', '',
            base64.b64encode(os.urandom(128)))[:64]
        settings.app.server_api_key = server_api_key
        settings.commit()
