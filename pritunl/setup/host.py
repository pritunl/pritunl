from pritunl import mongo
from pritunl import listener
from pritunl import settings

def _on_msg(msg):
    if msg['message'] != 'updated':
        return
    settings.local.host.load()

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

    listener.add_listener('hosts', _on_msg)
