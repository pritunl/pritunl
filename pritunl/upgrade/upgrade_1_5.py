from pritunl.upgrade.utils import get_collection

def upgrade_1_5():
    settings_collection = get_collection('settings')

    response = settings_collection.update_one({
        '_id': 'app',
        'sso': True,
    }, {'$set': {
        'sso': 'google',
    }})

    if not bool(response.modified_count):
        settings_collection.update_one({
            '_id': 'app',
        }, {'$set': {
            'sso': None,
        }})
