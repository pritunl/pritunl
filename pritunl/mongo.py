from constants import *
from exceptions import *
from pritunl import app_server
import pymongo
import re
import os
import base64

collections = {}

def setup_mongo():
    prefix = app_server.mongodb_collection_prefix or ''
    client = pymongo.MongoClient(app_server.mongodb_url)
    database = client.get_default_database()
    cur_collections = database.collection_names()

    if 'log_entries' not in cur_collections:
        database.create_collection(prefix + 'log_entries', capped=True,
            size=LOG_LIMIT * LOG_AVG_SIZE * 2, max=LOG_LIMIT)

    collections.update({
        'system': getattr(database, prefix + 'system'),
        'log_entries': getattr(database, prefix + 'log_entries'),
        'administrators': getattr(database, prefix + 'administrators'),
        'users': getattr(database, prefix + 'users'),
        'organizations': getattr(database, prefix + 'organizations'),
        'servers': getattr(database, prefix + 'servers'),
        'auth_nonces': getattr(database, prefix + 'auth_nonces'),
        'auth_limiter': getattr(database, prefix + 'auth_limiter'),
    })
    collections['log_entries'].ensure_index([
        ('time', pymongo.DESCENDING),
    ])
    collections['administrators'].ensure_index('username', unique=True)
    collections['users'].ensure_index([
        ('org_id', pymongo.ASCENDING),
        ('type', pymongo.ASCENDING),
    ])
    collections['users'].ensure_index([
        ('org_id', pymongo.ASCENDING),
        ('name', pymongo.ASCENDING),
    ])
    collections['organizations'].ensure_index('type')
    collections['servers'].ensure_index('name')
    collections['auth_nonces'].ensure_index([
        ('token', pymongo.ASCENDING),
        ('nonce', pymongo.ASCENDING),
    ], unique=True)
    collections['auth_nonces'].ensure_index('time',
        expireAfterSeconds=AUTH_NONCE_TIME_WINDOW * 2.1)
    collections['auth_limiter'].ensure_index('time',
        expireAfterSeconds=AUTH_LIMITER_TTL)

    from administrator import Administrator
    if not Administrator.get_collection().find_one():
        Administrator(
            username=DEFAULT_USERNAME,
            password=DEFAULT_PASSWORD,
            default=True,
        ).commit()

    from system_conf import SystemConf
    system_conf = SystemConf()
    secret_key = system_conf.get('app', 'cookie_secret')
    if not secret_key:
        secret_key = re.sub(r'[\W_]+', '',
            base64.b64encode(os.urandom(128)))[:64]
        system_conf.set('app', 'cookie_secret', secret_key)
        system_conf.commit()
    app_server.app.secret_key = secret_key.encode()

def get_collection(name):
    return collections[name]
