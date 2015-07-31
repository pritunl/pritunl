from pritunl import mongo

def setup_host():
    from pritunl import host
    collection = mongo.get_collection('settings')

    collection.update({
        '_id': 'subscription',
    }, {'$setOnInsert': {
        'active': None,
        'plan': None,
    }}, upsert=True)

    host.init()
