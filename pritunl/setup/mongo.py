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

def upsert_index(collection, index, **kwargs):
    try:
        collection.create_index(index, **kwargs)
    except:
        keys = pymongo.helpers._index_list(index)
        name = pymongo.helpers._gen_index_name(keys)
        collection.drop_index(name)
        collection.create_index(index, **kwargs)

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
                    read_preference=read_pref,
                )
            else:
                client = pymongo.MongoClient(
                    settings.conf.mongodb_uri,
                    connectTimeoutMS=MONGO_CONNECT_TIMEOUT,
                    socketTimeoutMS=MONGO_SOCKET_TIMEOUT,
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
                        read_preference=read_pref,
                    )
                else:
                    secondary_client = pymongo.MongoClient(
                        settings.conf.mongodb_uri,
                        connectTimeoutMS=MONGO_CONNECT_TIMEOUT,
                        socketTimeoutMS=MONGO_SOCKET_TIMEOUT,
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

    cur_collections = secondary_database.collection_names()
    if prefix + 'messages' not in cur_collections:
        secondary_database.create_collection(prefix + 'messages', capped=True,
            size=5000192, max=1500)

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
        'sso_tokens': getattr(secondary_database, prefix + 'sso_tokens'),
        'sso_cache': getattr(secondary_database, prefix + 'sso_cache'),
        'sso_client_cache': getattr(secondary_database,
            prefix + 'sso_client_cache'),
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

    upsert_index(mongo.collections['logs'], 'timestamp', background=True)
    upsert_index(mongo.collections['transaction'], 'lock_id',
        background=True, unique=True)
    upsert_index(mongo.collections['transaction'], [
        ('ttl_timestamp', pymongo.ASCENDING),
        ('state', pymongo.ASCENDING),
        ('priority', pymongo.DESCENDING),
    ], background=True)
    upsert_index(mongo.collections['queue'], 'runner_id', background=True)
    upsert_index(mongo.collections['queue'], 'ttl_timestamp', background=True)
    upsert_index(mongo.collections['tasks'], [
        ('ttl_timestamp', pymongo.ASCENDING),
        ('state', pymongo.ASCENDING),
    ], background=True)
    upsert_index(mongo.collections['log_entries'], [
        ('timestamp', pymongo.DESCENDING),
    ], background=True)
    upsert_index(mongo.collections['messages'], 'channel', background=True)
    upsert_index(mongo.collections['administrators'], 'username',
        background=True, unique=True)
    upsert_index(mongo.collections['users'], 'resource_id', background=True)
    upsert_index(mongo.collections['users'], [
        ('type', pymongo.ASCENDING),
        ('org_id', pymongo.ASCENDING),
    ], background=True)
    upsert_index(mongo.collections['users'], [
        ('org_id', pymongo.ASCENDING),
        ('name', pymongo.ASCENDING),
    ], background=True)
    upsert_index(mongo.collections['users_audit'], [
        ('org_id', pymongo.ASCENDING),
        ('user_id', pymongo.ASCENDING),
    ], background=True)
    upsert_index(mongo.collections['users_audit'], [
        ('timestamp', pymongo.DESCENDING),
    ], background=True)
    upsert_index(mongo.collections['users_key_link'], 'key_id',
        background=True)
    upsert_index(mongo.collections['users_key_link'], 'short_id',
        background=True, unique=True)
    upsert_index(mongo.collections['users_net_link'], 'user_id',
        background=True)
    upsert_index(mongo.collections['users_net_link'], 'org_id',
        background=True)
    upsert_index(mongo.collections['users_net_link'], 'network',
        background=True)
    upsert_index(mongo.collections['clients'], 'user_id', background=True)
    upsert_index(mongo.collections['clients'], 'domain', background=True)
    upsert_index(mongo.collections['clients'], 'virt_address_num',
        background=True)
    upsert_index(mongo.collections['clients'], [
        ('server_id', pymongo.ASCENDING),
        ('type', pymongo.ASCENDING),
    ], background=True)
    upsert_index(mongo.collections['clients'], [
        ('host_id', pymongo.ASCENDING),
        ('type', pymongo.ASCENDING),
    ], background=True)
    upsert_index(mongo.collections['clients_pool'],
        'client_id', background=True)
    upsert_index(mongo.collections['clients_pool'],
        'timestamp', background=True)
    upsert_index(mongo.collections['clients_pool'], [
        ('server_id', pymongo.ASCENDING),
        ('user_id', pymongo.ASCENDING),
    ], background=True)
    upsert_index(mongo.collections['organizations'], 'type', background=True)
    upsert_index(mongo.collections['organizations'],
        'auth_token', background=True)
    upsert_index(mongo.collections['hosts'], 'name', background=True)
    upsert_index(mongo.collections['hosts_usage'], [
        ('host_id', pymongo.ASCENDING),
        ('timestamp', pymongo.ASCENDING),
    ], background=True)
    upsert_index(mongo.collections['servers'], 'name', background=True)
    upsert_index(mongo.collections['servers'], 'ping_timestamp',
        background=True)
    upsert_index(mongo.collections['servers_output'], [
        ('server_id', pymongo.ASCENDING),
        ('timestamp', pymongo.ASCENDING),
    ], background=True)
    upsert_index(mongo.collections['servers_output_link'], [
        ('server_id', pymongo.ASCENDING),
        ('timestamp', pymongo.ASCENDING),
    ], background=True)
    upsert_index(mongo.collections['servers_bandwidth'], [
        ('server_id', pymongo.ASCENDING),
        ('period', pymongo.ASCENDING),
        ('timestamp', pymongo.ASCENDING),
    ], background=True)
    upsert_index(mongo.collections['servers_ip_pool'], [
        ('server_id', pymongo.ASCENDING),
        ('user_id', pymongo.ASCENDING),
    ], background=True)
    upsert_index(mongo.collections['servers_ip_pool'], [
        ('server_id', pymongo.ASCENDING),
        ('_id', pymongo.DESCENDING),
    ], background=True)
    upsert_index(mongo.collections['servers_ip_pool'], 'user_id',
        background=True)
    upsert_index(mongo.collections['routes_reserve'], 'timestamp',
        background=True)
    upsert_index(mongo.collections['dh_params'], 'dh_param_bits',
        background=True)
    upsert_index(mongo.collections['auth_nonces'], [
        ('token', pymongo.ASCENDING),
        ('nonce', pymongo.ASCENDING),
    ], background=True, unique=True)
    upsert_index(mongo.collections['sso_cache'], [
        ('user_id', pymongo.ASCENDING),
        ('server_id', pymongo.ASCENDING),
    ], background=True)
    upsert_index(mongo.collections['sso_cache'], [
        ('user_id', pymongo.ASCENDING),
        ('server_id', pymongo.ASCENDING),
    ], background=True)
    upsert_index(mongo.collections['vxlans'], 'server_id',
        background=True, unique=True)

    upsert_index(mongo.collections['tasks'], 'timestamp',
        background=True, expireAfterSeconds=300)
    upsert_index(mongo.collections['clients'], 'timestamp',
        background=True, expireAfterSeconds=settings.vpn.client_ttl)
    upsert_index(mongo.collections['users_key_link'], 'timestamp',
        background=True, expireAfterSeconds=settings.app.key_link_timeout)
    upsert_index(mongo.collections['auth_sessions'], 'timestamp',
        background=True, expireAfterSeconds=settings.app.session_timeout)
    upsert_index(mongo.collections['auth_nonces'], 'timestamp',
        background=True,
        expireAfterSeconds=settings.app.auth_time_window * 2.1)
    upsert_index(mongo.collections['auth_limiter'], 'timestamp',
        background=True, expireAfterSeconds=settings.app.auth_limiter_ttl)
    upsert_index(mongo.collections['otp'], 'timestamp', background=True,
        expireAfterSeconds=120)
    upsert_index(mongo.collections['otp_cache'], 'timestamp', background=True,
        expireAfterSeconds=settings.user.otp_cache_ttl)
    upsert_index(mongo.collections['sso_tokens'], 'timestamp', background=True,
        expireAfterSeconds=600)
    upsert_index(mongo.collections['sso_cache'], 'timestamp',
        background=True, expireAfterSeconds=settings.app.sso_cache_timeout)
    upsert_index(mongo.collections['sso_client_cache'], 'timestamp',
        background=True,
        expireAfterSeconds=settings.app.sso_client_cache_timeout + 21600)

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
