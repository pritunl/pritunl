from pritunl.app_server import app_server
from pritunl.settings import settings
from pritunl import logger
from pritunl import mongo

import pymongo
import bson
import re
import os
import base64
import flask
import random

def setup_mongo():
    # TODO move this
    if not pymongo.has_c():
        logger.warning('Failed to load pymongo c bindings')

    if not bson.has_c():
        logger.warning('Failed to load bson c bindings')

    prefix = settings.conf.mongodb_collection_prefix or ''
    client = pymongo.MongoClient(settings.conf.mongodb_url,
        connectTimeoutMS=500) # TODO
    database = client.get_default_database()
    cur_collections = database.collection_names()

    mongo.collections.update({
        'transaction': getattr(database, prefix + 'transaction'),
        'queue': getattr(database, prefix + 'queue'),
        'task': getattr(database, prefix + 'task'),
        'system': getattr(database, prefix + 'system'),
        'messages': getattr(database, prefix + 'messages'),
        'log_entries': getattr(database, prefix + 'log_entries'),
        'administrators': getattr(database, prefix + 'administrators'),
        'users': getattr(database, prefix + 'users'),
        'organizations': getattr(database, prefix + 'organizations'),
        'hosts': getattr(database, prefix + 'hosts'),
        'hosts_usage': getattr(database, prefix + 'hosts_usage'),
        'servers': getattr(database, prefix + 'servers'),
        'servers_bandwidth': getattr(database, prefix + 'servers_bandwidth'),
        'servers_ip_pool': getattr(database, prefix + 'servers_ip_pool'),
        'dh_params': getattr(database, prefix + 'dh_params'),
        'auth_nonces': getattr(database, prefix + 'auth_nonces'),
        'auth_limiter': getattr(database, prefix + 'auth_limiter'),
    })

    for collection_name, collection in mongo.collections.items():
        collection.name_str = collection_name

    settings.start()
    settings.commit(True)

    if prefix + 'log_entries' not in cur_collections:
        log_limit = settings.app.log_entry_limit
        database.create_collection(prefix + 'log_entries', capped=True,
            size=log_limit * 256 * 2, max=log_limit)

    if prefix + 'messages' not in cur_collections:
        database.create_collection(prefix + 'messages', capped=True,
            size=100000)

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

    from pritunl.administrator import Administrator
    if not Administrator.collection.find_one():
        Administrator(
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
    app_server.app.secret_key = secret_key.encode()

    server_api_key = settings.app.email_api_key
    if not server_api_key:
        server_api_key = re.sub(r'[\W_]+', '',
            base64.b64encode(os.urandom(128)))[:64]
        settings.app.email_api_key = server_api_key
        settings.commit()
    app_server.server_api_key = server_api_key
