from constants import *
from exceptions import *
from pritunl import app_server
import pymongo

collections = {}

def setup_mongo():
    client = pymongo.MongoClient(app_server.mongodb_url)
    database = client.get_default_database()

    collections.update({
        'system': database.system,
        'administrators': database.administrators,
        'users': database.users,
        'organizations': database.organizations,
        'servers': database.servers,
        'auth_nonces': database.auth_nonces,
    })
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
    collections['auth_nonces'].ensure_index('timestamp',
        expireAfterSeconds=AUTH_TIME_WINDOW * 2.1)

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
