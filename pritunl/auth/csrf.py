from pritunl import utils
from pritunl import mongo

def get_token():
    coll = mongo.get_collection('auth_csrf_tokens')
    token = utils.generate_secret()

    coll.insert({
        '_id': token,
        'timestamp': utils.now(),
    })

    return token

def validate_token(token):
    coll = mongo.get_collection('auth_csrf_tokens')

    return bool(coll.find_one({
        '_id': token,
    }))
