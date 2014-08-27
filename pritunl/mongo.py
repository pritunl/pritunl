from constants import *
from exceptions import *
from pritunl import app_server
import pymongo
import re
import os
import base64
import flask

collections = {}

insert_orig = pymongo.collection.Collection.insert
def insert(self, *args, **kwargs):
    if flask.ctx.has_request_context():
         flask.g.query_count += 1
    return insert_orig(self, *args, **kwargs)
pymongo.collection.Collection.insert = insert

update_orig = pymongo.collection.Collection.update
def update(self, *args, **kwargs):
    if flask.ctx.has_request_context():
         flask.g.query_count += 1
    return update_orig(self, *args, **kwargs)
pymongo.collection.Collection.update = update

remove_orig = pymongo.collection.Collection.remove
def remove(self, *args, **kwargs):
    if flask.ctx.has_request_context():
         flask.g.query_count += 1
    return remove_orig(self, *args, **kwargs)
pymongo.collection.Collection.remove = remove

find_orig = pymongo.collection.Collection.find
def find(self, *args, **kwargs):
    if flask.ctx.has_request_context():
         flask.g.query_count += 1
    return find_orig(self, *args, **kwargs)
pymongo.collection.Collection.find = find

def setup_mongo():
    prefix = app_server.mongodb_collection_prefix or ''
    client = pymongo.MongoClient(app_server.mongodb_url)
    database = client.get_default_database()
    cur_collections = database.collection_names()

    if prefix + 'log_entries' not in cur_collections:
        database.create_collection(prefix + 'log_entries', capped=True,
            size=LOG_LIMIT * LOG_AVG_SIZE * 2, max=LOG_LIMIT)

    if prefix + 'messages' not in cur_collections:
        database.create_collection(prefix + 'messages', capped=True,
            size=100000)

    collections.update({
        'transaction': getattr(database, prefix + 'transaction'),
        'system': getattr(database, prefix + 'system'),
        'messages': getattr(database, prefix + 'messages'),
        'log_entries': getattr(database, prefix + 'log_entries'),
        'administrators': getattr(database, prefix + 'administrators'),
        'users': getattr(database, prefix + 'users'),
        'organizations': getattr(database, prefix + 'organizations'),
        'servers': getattr(database, prefix + 'servers'),
        'servers_bandwidth': getattr(database, prefix + 'servers_bandwidth'),
        'auth_nonces': getattr(database, prefix + 'auth_nonces'),
        'auth_limiter': getattr(database, prefix + 'auth_limiter'),
    })
    collections['transaction'].ensure_index('state')
    collections['transaction'].ensure_index([
        ('timestamp', pymongo.ASCENDING),
        ('state', pymongo.ASCENDING),
        ('priority', pymongo.DESCENDING),
    ])
    collections['log_entries'].ensure_index([
        ('timestamp', pymongo.DESCENDING),
    ])
    collections['messages'].ensure_index('channel')
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
    collections['servers_bandwidth'].ensure_index([
        ('server_id', pymongo.ASCENDING),
        ('period', pymongo.ASCENDING),
        ('timestamp', pymongo.ASCENDING),
    ])
    collections['auth_nonces'].ensure_index([
        ('token', pymongo.ASCENDING),
        ('nonce', pymongo.ASCENDING),
    ], unique=True)
    collections['auth_nonces'].ensure_index('timestamp',
        expireAfterSeconds=AUTH_NONCE_TIME_WINDOW * 2.1)
    collections['auth_limiter'].ensure_index('timestamp',
        expireAfterSeconds=AUTH_LIMITER_TTL)

    from administrator import Administrator
    if not Administrator.collection.find_one():
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

    server_api_key = system_conf.get('app', 'server_api_key')
    if not server_api_key:
        server_api_key = re.sub(r'[\W_]+', '',
            base64.b64encode(os.urandom(128)))[:64]
        system_conf.set('app', 'server_api_key', server_api_key)
        system_conf.commit()
    app_server.server_api_key = server_api_key

def get_collection(name):
    return collections[name]
