from pritunl import mongo

def setup_server_fix():
    servers_collection = mongo.get_collection('servers')

    servers_collection.update({}, {'$set': {
        'pool_cursor': None,
    }})
