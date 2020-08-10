from pritunl.constants import *
from pritunl import app
from pritunl import settings
from pritunl import logger
from pritunl import mongo
from pritunl import auth
from pritunl import utils

import pymongo
import pymongo.helpers
import time
import collections

def _get_read_pref(name):
    return {
        'primary': \
            pymongo.read_preferences.ReadPreference.PRIMARY,
        'primaryPreferred': \
            pymongo.read_preferences.ReadPreference.PRIMARY_PREFERRED,
        'secondary': \
            pymongo.read_preferences.ReadPreference.SECONDARY,
        'secondaryPreferred': \
            pymongo.read_preferences.ReadPreference.SECONDARY_PREFERRED,
        'nearest': \
            pymongo.read_preferences.ReadPreference.NEAREST,
    }.get(name)

coll_indexes = collections.defaultdict(set)

def upsert_index(coll_name, index, **kwargs):
    coll = mongo.get_collection(coll_name)

    keys = pymongo.helpers._index_list(index)
    name = pymongo.helpers._gen_index_name(keys)
    coll_indexes[coll_name].add(name)

    try:
        coll.create_index(index, **kwargs)
    except:
        try:
            keys = pymongo.helpers._index_list(index)
            name = pymongo.helpers._gen_index_name(keys)
            coll.drop_index(name)
        except:
            pass
        coll.create_index(index, **kwargs)

def drop_index(coll, index, **kwargs):
    try:
        keys = pymongo.helpers._index_list(index)
        name = pymongo.helpers._gen_index_name(keys)
        coll.drop_index(name)
    except:
        pass

def clean_indexes():
    for coll_name in list(mongo.collection_types.keys()):
        coll = mongo.get_collection(coll_name)
        indexes = coll_indexes[coll_name]

        try:
            for index in coll.list_indexes():
                name = index['name']
                if name == '_id' or name == '_id_' or name in indexes:
                    continue

                coll.drop_index(name)
        except pymongo.errors.OperationFailure:
            pass

def upsert_indexes():
    prefix = settings.conf.mongodb_collection_prefix or ''
    mongo.prefix = prefix

    cur_collections = mongo.database.collection_names()
    if prefix + 'logs' not in cur_collections:
        log_limit = settings.app.log_limit
        mongo.database.create_collection(prefix + 'logs', capped=True,
            size=log_limit * 1024, max=log_limit)

    if prefix + 'log_entries' not in cur_collections:
        log_entry_limit = settings.app.log_entry_limit
        mongo.database.create_collection(prefix + 'log_entries', capped=True,
            size=log_entry_limit * 512, max=log_entry_limit)

    cur_collections = mongo.secondary_database.collection_names()
    if prefix + 'messages' not in cur_collections:
        mongo.secondary_database.create_collection(
            prefix + 'messages', capped=True,
            size=5000192, max=1000)

    upsert_index('logs', 'timestamp', background=True)
    upsert_index('transaction', 'lock_id',
        background=True, unique=True)
    upsert_index('transaction', [
        ('ttl_timestamp', pymongo.ASCENDING),
        ('state', pymongo.ASCENDING),
        ('priority', pymongo.DESCENDING),
    ], background=True)
    upsert_index('queue', 'runner_id', background=True)
    upsert_index('queue', 'ttl_timestamp', background=True)
    upsert_index('queue', [
        ('priority', pymongo.ASCENDING),
        ('ttl_timestamp', pymongo.ASCENDING),
    ], background=True)
    upsert_index('tasks', [
        ('ttl_timestamp', pymongo.ASCENDING),
    ], background=True)
    upsert_index('tasks', [
        ('ttl_timestamp', pymongo.ASCENDING),
        ('state', pymongo.ASCENDING),
    ], background=True)
    upsert_index('log_entries', [
        ('timestamp', pymongo.DESCENDING),
    ], background=True)
    upsert_index('messages', 'channel', background=True)
    upsert_index('administrators', 'username',
        background=True, unique=True)
    upsert_index('users', 'resource_id', background=True)
    upsert_index('users', [
        ('type', pymongo.ASCENDING),
        ('org_id', pymongo.ASCENDING),
    ], background=True)
    upsert_index('users', [
        ('org_id', pymongo.ASCENDING),
        ('name', pymongo.ASCENDING),
    ], background=True)
    upsert_index('users', [
        ('name', pymongo.ASCENDING),
        ('auth_type', pymongo.ASCENDING),
    ], background=True)
    upsert_index('users_audit', [
        ('org_id', pymongo.ASCENDING),
        ('user_id', pymongo.ASCENDING),
    ], background=True)
    upsert_index('users_audit', [
        ('timestamp', pymongo.DESCENDING),
    ], background=True)
    upsert_index('users_key_link', [
        ('org_id', pymongo.ASCENDING),
        ('user_id', pymongo.ASCENDING),
    ], background=True)
    upsert_index('users_key_link', 'key_id',
        background=True)
    upsert_index('users_key_link', 'short_id',
        background=True, unique=True)
    upsert_index('users_net_link', 'user_id',
        background=True)
    upsert_index('users_net_link', 'org_id',
        background=True)
    upsert_index('users_net_link', 'network',
        background=True)
    upsert_index('clients', 'user_id', background=True)
    upsert_index('clients', 'domain', background=True)
    upsert_index('clients', 'virt_address_num',
        background=True)
    upsert_index('clients', [
        ('server_id', pymongo.ASCENDING),
        ('type', pymongo.ASCENDING),
    ], background=True)
    upsert_index('clients', [
        ('host_id', pymongo.ASCENDING),
        ('type', pymongo.ASCENDING),
    ], background=True)
    upsert_index('clients_pool',
        'client_id', background=True)
    upsert_index('clients_pool',
        'timestamp', background=True)
    upsert_index('clients_pool', [
        ('server_id', pymongo.ASCENDING),
        ('user_id', pymongo.ASCENDING),
    ], background=True)
    upsert_index('organizations', 'type', background=True)
    upsert_index('organizations',
        'auth_token', background=True)
    upsert_index('hosts', 'name', background=True)
    upsert_index('hosts_usage', [
        ('host_id', pymongo.ASCENDING),
        ('timestamp', pymongo.ASCENDING),
    ], background=True)
    upsert_index('servers', 'name', background=True)
    upsert_index('servers', 'ping_timestamp',
        background=True)
    upsert_index('servers_output', [
        ('server_id', pymongo.ASCENDING),
        ('timestamp', pymongo.ASCENDING),
    ], background=True)
    upsert_index('servers_output_link', [
        ('server_id', pymongo.ASCENDING),
        ('timestamp', pymongo.ASCENDING),
    ], background=True)
    upsert_index('servers_bandwidth', [
        ('server_id', pymongo.ASCENDING),
        ('period', pymongo.ASCENDING),
        ('timestamp', pymongo.ASCENDING),
    ], background=True)
    upsert_index('servers_ip_pool', [
        ('server_id', pymongo.ASCENDING),
        ('user_id', pymongo.ASCENDING),
    ], background=True)
    upsert_index('servers_ip_pool', [
        ('server_id', pymongo.ASCENDING),
        ('_id', pymongo.DESCENDING),
    ], background=True)
    upsert_index('servers_ip_pool', 'user_id',
        background=True)
    upsert_index('links_hosts', 'link_id',
        background=True)
    upsert_index('links_hosts', [
        ('location_id', pymongo.ASCENDING),
        ('status', pymongo.ASCENDING),
        ('active', pymongo.ASCENDING),
        ('priority', pymongo.DESCENDING),
    ], background=True)
    upsert_index('links_hosts', [
        ('location_id', pymongo.ASCENDING),
        ('static', pymongo.ASCENDING),
    ], background=True)
    upsert_index('links_hosts', [
        ('location_id', pymongo.ASCENDING),
        ('name', pymongo.ASCENDING),
    ], background=True)
    upsert_index('links_hosts', 'ping_timestamp_ttl',
        background=True)
    upsert_index('links_locations', 'link_id',
        background=True)
    upsert_index('routes_reserve', 'timestamp',
        background=True)
    upsert_index('dh_params', 'dh_param_bits',
        background=True)
    upsert_index('auth_nonces', [
        ('token', pymongo.ASCENDING),
        ('nonce', pymongo.ASCENDING),
    ], background=True, unique=True)
    upsert_index('otp_cache', [
        ('user_id', pymongo.ASCENDING),
        ('server_id', pymongo.ASCENDING),
    ], background=True)
    upsert_index('sso_push_cache', [
        ('user_id', pymongo.ASCENDING),
        ('server_id', pymongo.ASCENDING),
    ], background=True)
    upsert_index('sso_client_cache', [
        ('user_id', pymongo.ASCENDING),
        ('server_id', pymongo.ASCENDING),
    ], background=True)
    upsert_index('sso_passcode_cache', [
        ('user_id', pymongo.ASCENDING),
        ('server_id', pymongo.ASCENDING),
    ], background=True)
    upsert_index('vxlans', 'server_id',
        background=True, unique=True)

    upsert_index('tasks', 'timestamp',
        background=True, expireAfterSeconds=300)
    if settings.app.demo_mode:
        drop_index(mongo.get_collection('clients'),
            'timestamp', background=True)
    else:
        upsert_index('clients', 'timestamp',
            background=True, expireAfterSeconds=settings.vpn.client_ttl)
        upsert_index('clients_pool', 'timestamp',
            background=True, expireAfterSeconds=settings.vpn.client_ttl)
    upsert_index('users_key_link', 'timestamp',
        background=True, expireAfterSeconds=settings.app.key_link_timeout)
    upsert_index('acme_challenges', 'timestamp',
        background=True, expireAfterSeconds=180)
    upsert_index('auth_sessions', 'timestamp',
        background=True, expireAfterSeconds=settings.app.session_timeout)
    upsert_index('auth_nonces', 'timestamp',
        background=True,
        expireAfterSeconds=max(
            settings.app.auth_time_window * 2,
            settings.app.auth_expire_window,
        ))
    upsert_index('auth_csrf_tokens', 'timestamp',
        background=True, expireAfterSeconds=604800)
    upsert_index('auth_limiter', 'timestamp',
        background=True, expireAfterSeconds=settings.app.auth_limiter_ttl)
    upsert_index('wg_keys', 'timestamp',
        background=True, expireAfterSeconds=settings.app.wg_public_key_ttl)
    upsert_index('otp', 'timestamp', background=True,
        expireAfterSeconds=120)
    upsert_index('otp_cache', 'timestamp',
        background=True, expireAfterSeconds=settings.app.sso_cache_timeout)
    upsert_index('yubikey', 'timestamp',
        background=True, expireAfterSeconds=86400)
    upsert_index('sso_tokens', 'timestamp',
        background=True, expireAfterSeconds=600)
    upsert_index('sso_push_cache', 'timestamp',
        background=True, expireAfterSeconds=settings.app.sso_cache_timeout)
    upsert_index('sso_client_cache', 'timestamp',
        background=True,
        expireAfterSeconds=settings.app.sso_client_cache_timeout +
            settings.app.sso_client_cache_window)
    upsert_index('sso_passcode_cache', 'timestamp',
        background=True, expireAfterSeconds=settings.app.sso_cache_timeout)

    try:
        clean_indexes()
    except:
        logger.exception('Failed to clean indexes', 'setup')

def setup_mongo():
    prefix = settings.conf.mongodb_collection_prefix or ''
    read_pref = _get_read_pref(settings.conf.mongodb_read_preference)
    max_pool = settings.conf.mongodb_max_pool_size or None
    last_error = time.time() - 24

    while True:
        try:

            if read_pref:
                client = pymongo.MongoClient(
                    settings.conf.mongodb_uri,
                    connectTimeoutMS=MONGO_CONNECT_TIMEOUT,
                    socketTimeoutMS=MONGO_SOCKET_TIMEOUT,
                    serverSelectionTimeoutMS=MONGO_SOCKET_TIMEOUT,
                    maxPoolSize=max_pool,
                    read_preference=read_pref,
                )
            else:
                client = pymongo.MongoClient(
                    settings.conf.mongodb_uri,
                    connectTimeoutMS=MONGO_CONNECT_TIMEOUT,
                    socketTimeoutMS=MONGO_SOCKET_TIMEOUT,
                    serverSelectionTimeoutMS=MONGO_SOCKET_TIMEOUT,
                    maxPoolSize=max_pool,
                )

            break
        except pymongo.errors.ConnectionFailure:
            time.sleep(0.5)
            if time.time() - last_error > 30:
                last_error = time.time()
                logger.exception('Error connecting to mongodb server')

    database = client.get_default_database()

    settings_col = getattr(database, prefix + 'settings')
    app_settings = settings_col.find_one({'_id': 'app'})
    if app_settings:
        secondary_mongodb_uri = app_settings.get('secondary_mongodb_uri')
    else:
        secondary_mongodb_uri = None

    if secondary_mongodb_uri:
        while True:
            try:
                read_pref = _get_read_pref(
                    settings.conf.mongodb_read_preference)

                if read_pref:
                    secondary_client = pymongo.MongoClient(
                        secondary_mongodb_uri,
                        connectTimeoutMS=MONGO_CONNECT_TIMEOUT,
                        socketTimeoutMS=MONGO_SOCKET_TIMEOUT,
                        serverSelectionTimeoutMS=MONGO_SOCKET_TIMEOUT,
                        maxPoolSize=max_pool,
                        read_preference=read_pref,
                    )
                else:
                    secondary_client = pymongo.MongoClient(
                        secondary_mongodb_uri,
                        connectTimeoutMS=MONGO_CONNECT_TIMEOUT,
                        socketTimeoutMS=MONGO_SOCKET_TIMEOUT,
                        serverSelectionTimeoutMS=MONGO_SOCKET_TIMEOUT,
                        maxPoolSize=max_pool,
                    )

                break
            except pymongo.errors.ConnectionFailure:
                time.sleep(0.5)
                if time.time() - last_error > 30:
                    last_error = time.time()
                    logger.exception(
                        'Error connecting to secondary mongodb server')

        secondary_database = secondary_client.get_default_database()
    else:
        secondary_database = database

    mongo.database = database
    mongo.secondary_database = secondary_database

    cur_collections = database.collection_names()
    cur_sec_collections = secondary_database.collection_names()
    if 'authorities' in cur_collections or \
            'authorities' in cur_sec_collections:
        raise TypeError('Cannot connect to a Pritunl Zero database')

    mongo.collection_types = {
        'transaction': 1,
        'queue': 1,
        'tasks': 1,
        'settings': 1,
        'messages': 2,
        'administrators': 1,
        'users': 1,
        'users_audit': 1,
        'users_key_link': 2,
        'users_net_link': 1,
        'clients': 1,
        'clients_pool': 1,
        'organizations': 1,
        'hosts': 1,
        'hosts_usage': 1,
        'servers': 1,
        'servers_output': 1,
        'servers_output_link': 1,
        'servers_bandwidth': 1,
        'servers_ip_pool': 1,
        'links': 1,
        'links_locations': 1,
        'links_hosts': 1,
        'routes_reserve': 1,
        'dh_params': 1,
        'acme_challenges': 1,
        'auth_sessions': 2,
        'auth_csrf_tokens': 2,
        'auth_nonces': 2,
        'auth_limiter': 2,
        'wg_keys': 2,
        'otp': 2,
        'otp_cache': 2,
        'yubikey': 2,
        'sso_tokens': 2,
        'sso_push_cache': 2,
        'sso_client_cache': 2,
        'sso_passcode_cache': 2,
        'vxlans': 1,
        'logs': 1,
        'log_entries': 1,
    }

    cur_collections = mongo.secondary_database.collection_names()
    if prefix + 'messages' not in cur_collections:
        mongo.secondary_database.create_collection(
            prefix + 'messages', capped=True,
            size=5000192, max=1000)
    elif not mongo.get_collection('messages').options().get('capped'):
        mongo.get_collection('messages').drop()
        mongo.secondary_database.create_collection(
            prefix + 'messages', capped=True,
            size=5000192, max=1000)

    settings.local.mongo_time = None

    while True:
        try:
            utils.sync_time()
            break
        except:
            logger.exception('Failed to sync time', 'setup')
            time.sleep(30)

    settings.init()

    upsert_indexes()

    if not auth.Administrator.collection.find_one():
        default_admin = auth.Administrator(
            username=DEFAULT_USERNAME,
        )
        default_admin.generate_default_password()
        default_admin.commit()

    secret_key = settings.app.cookie_secret
    secret_key2 = settings.app.cookie_secret2
    settings_commit = False

    if not secret_key:
        settings_commit = True
        secret_key = utils.rand_str(64)
        settings.app.cookie_secret = secret_key

    if not secret_key2:
        settings_commit = True
        settings.app.cookie_secret2 = utils.rand_str(64)

    if settings_commit:
        settings.commit()

    app.app.secret_key = secret_key.encode()
