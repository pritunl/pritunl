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
    coll = mongo.collections[coll_name]

    keys = pymongo.helpers._index_list(index)
    name = pymongo.helpers._gen_index_name(keys)
    coll_indexes[coll_name].add(name)

    try:
        coll.create_index(index, **kwargs)
    except:
        keys = pymongo.helpers._index_list(index)
        name = pymongo.helpers._gen_index_name(keys)
        coll.drop_index(name)
        coll.create_index(index, **kwargs)

def drop_index(coll, index, **kwargs):
    try:
        keys = pymongo.helpers._index_list(index)
        name = pymongo.helpers._gen_index_name(keys)
        coll.drop_index(name)
    except:
        pass

def clean_indexes():
    for coll_name, coll in mongo.collections.items():
        indexes = coll_indexes[coll_name]

        try:
            for index in coll.list_indexes():
                name = index['name']
                if name == '_id' or name == '_id_' or name in indexes:
                    continue

                coll.drop_index(name)
        except pymongo.errors.OperationFailure:
            pass

def setup_mongo():
    prefix = settings.conf.mongodb_collection_prefix or ''
    last_error = time.time() - 24

    while True:
        try:
            read_pref = _get_read_pref(settings.conf.mongodb_read_preference)

            if read_pref:
                client = pymongo.MongoClient(
                    settings.conf.mongodb_uri,
                    connectTimeoutMS=MONGO_CONNECT_TIMEOUT,
                    socketTimeoutMS=MONGO_SOCKET_TIMEOUT,
                    serverSelectionTimeoutMS=MONGO_SOCKET_TIMEOUT,
                    read_preference=read_pref,
                )
            else:
                client = pymongo.MongoClient(
                    settings.conf.mongodb_uri,
                    connectTimeoutMS=MONGO_CONNECT_TIMEOUT,
                    socketTimeoutMS=MONGO_SOCKET_TIMEOUT,
                    serverSelectionTimeoutMS=MONGO_SOCKET_TIMEOUT,
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
                        settings.conf.mongodb_uri,
                        connectTimeoutMS=MONGO_CONNECT_TIMEOUT,
                        socketTimeoutMS=MONGO_SOCKET_TIMEOUT,
                        serverSelectionTimeoutMS=MONGO_SOCKET_TIMEOUT,
                        read_preference=read_pref,
                    )
                else:
                    secondary_client = pymongo.MongoClient(
                        settings.conf.mongodb_uri,
                        connectTimeoutMS=MONGO_CONNECT_TIMEOUT,
                        socketTimeoutMS=MONGO_SOCKET_TIMEOUT,
                        serverSelectionTimeoutMS=MONGO_SOCKET_TIMEOUT,
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

    cur_collections = secondary_database.collection_names()
    if prefix + 'messages' not in cur_collections:
        secondary_database.create_collection(prefix + 'messages', capped=True,
            size=5000192, max=1000)

    mongo.collections.update({
        'transaction': getattr(database, prefix + 'transaction'),
        'queue': getattr(database, prefix + 'queue'),
        'tasks': getattr(database, prefix + 'tasks'),
        'settings': getattr(database, prefix + 'settings'),
        'messages': getattr(secondary_database, prefix + 'messages'),
        'administrators': getattr(database, prefix + 'administrators'),
        'users': getattr(database, prefix + 'users'),
        'users_audit': getattr(database, prefix + 'users_audit'),
        'users_key_link': getattr(secondary_database,
            prefix + 'users_key_link'),
        'users_net_link': getattr(database, prefix + 'users_net_link'),
        'clients': getattr(database, prefix + 'clients'),
        'clients_pool': getattr(database, prefix + 'clients_pool'),
        'organizations': getattr(database, prefix + 'organizations'),
        'hosts': getattr(database, prefix + 'hosts'),
        'hosts_usage': getattr(database, prefix + 'hosts_usage'),
        'servers': getattr(database, prefix + 'servers'),
        'servers_output': getattr(database, prefix + 'servers_output'),
        'servers_output_link': getattr(database,
            prefix + 'servers_output_link'),
        'servers_bandwidth': getattr(database, prefix + 'servers_bandwidth'),
        'servers_ip_pool': getattr(database, prefix + 'servers_ip_pool'),
        'links': getattr(database, prefix + 'links'),
        'links_locations': getattr(database, prefix + 'links_locations'),
        'links_hosts': getattr(database, prefix + 'links_hosts'),
        'routes_reserve': getattr(database, prefix + 'routes_reserve'),
        'dh_params': getattr(database, prefix + 'dh_params'),
        'auth_sessions': getattr(secondary_database,
            prefix + 'auth_sessions'),
        'auth_csrf_tokens': getattr(secondary_database,
            prefix + 'auth_csrf_tokens'),
        'auth_nonces': getattr(secondary_database, prefix + 'auth_nonces'),
        'auth_limiter': getattr(secondary_database, prefix + 'auth_limiter'),
        'otp': getattr(secondary_database, prefix + 'otp'),
        'otp_cache': getattr(secondary_database, prefix + 'otp_cache'),
        'yubikey': getattr(secondary_database, prefix + 'yubikey'),
        'sso_tokens': getattr(secondary_database, prefix + 'sso_tokens'),
        'sso_push_cache': getattr(secondary_database,
            prefix + 'sso_push_cache'),
        'sso_client_cache': getattr(secondary_database,
            prefix + 'sso_client_cache'),
        'sso_passcode_cache': getattr(secondary_database,
            prefix + 'sso_passcode_cache'),
        'vxlans': getattr(database, prefix + 'vxlans'),
    })

    for collection_name, collection in mongo.collections.items():
        collection.name_str = collection_name

    settings.local.mongo_time = None

    while True:
        try:
            utils.sync_time()
            break
        except:
            logger.exception('Failed to sync time', 'setup')
            time.sleep(30)

    settings.init()

    cur_collections = database.collection_names()
    if prefix + 'logs' not in cur_collections:
        log_limit = settings.app.log_limit
        database.create_collection(prefix + 'logs', capped=True,
            size=log_limit * 1024, max=log_limit)

    if prefix + 'log_entries' not in cur_collections:
        log_entry_limit = settings.app.log_entry_limit
        database.create_collection(prefix + 'log_entries', capped=True,
            size=log_entry_limit * 512, max=log_entry_limit)

    mongo.collections.update({
        'logs': getattr(database, prefix + 'logs'),
        'log_entries': getattr(database, prefix + 'log_entries'),
    })
    mongo.collections['logs'].name_str = 'logs'
    mongo.collections['log_entries'].name_str = 'log_entries'

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
        drop_index(mongo.collections['clients'], 'timestamp', background=True)
    else:
        upsert_index('clients', 'timestamp',
            background=True, expireAfterSeconds=settings.vpn.client_ttl)
    upsert_index('users_key_link', 'timestamp',
        background=True, expireAfterSeconds=settings.app.key_link_timeout)
    upsert_index('auth_sessions', 'timestamp',
        background=True, expireAfterSeconds=settings.app.session_timeout)
    upsert_index('auth_nonces', 'timestamp',
        background=True,
        expireAfterSeconds=settings.app.auth_time_window * 2.1)
    upsert_index('auth_csrf_tokens', 'timestamp',
        background=True, expireAfterSeconds=604800)
    upsert_index('auth_limiter', 'timestamp',
        background=True, expireAfterSeconds=settings.app.auth_limiter_ttl)
    upsert_index('otp', 'timestamp', background=True,
        expireAfterSeconds=120)
    upsert_index('otp_cache', 'timestamp',
        background=True, expireAfterSeconds=settings.vpn.otp_cache_timeout)
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

    if not auth.Administrator.collection.find_one():
        auth.Administrator(
            username=DEFAULT_USERNAME,
            password=DEFAULT_PASSWORD,
            default=True,
        ).commit()

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
