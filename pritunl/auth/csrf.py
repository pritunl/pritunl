from pritunl import utils
from pritunl import mongo

def get_token(admin_id):
    coll = mongo.get_collection('auth_csrf_tokens')
    token = utils.generate_secret()

    coll.insert({
        '_id': token,
        'admin_id': admin_id,
        'timestamp': utils.now(),
    })

    return token

def validate_token(admin_id, token):
    coll = mongo.get_collection('auth_csrf_tokens')

    return bool(coll.find_one({
        '_id': token,
        'admin_id': admin_id,
    }))
