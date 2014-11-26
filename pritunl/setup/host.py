from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.helpers import *
from pritunl import mongo

def setup_host():
    collection = mongo.get_collection('settings')

    collection.update({
        '_id': 'subscription',
    }, {'$setOnInsert': {
        'active': None,
        'plan': None,
    }}, upsert=True)

    from pritunl import host
    host.init()
