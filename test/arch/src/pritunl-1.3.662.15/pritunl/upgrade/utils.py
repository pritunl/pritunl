from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *
from pritunl import settings

import pymongo
import bson

_prefix = None
_database = None

def _database_setup():
    global _prefix
    global _database

    _prefix = settings.conf.mongodb_collection_prefix or ''
    client = pymongo.MongoClient(settings.conf.mongodb_uri,
        connectTimeoutMS=MONGO_CONNECT_TIMEOUT)
    _database = client.get_default_database()

def get_collection(collection):
    if _database is None:
        _database_setup()
    return getattr(_database, _prefix + collection)
