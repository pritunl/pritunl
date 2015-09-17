from pritunl.upgrade.utils import get_collection

def upgrade_1_5():
    settings_collection = get_collection('settings')

    response = settings_collection.update({
        '_id': 'app',
        'sso': True,
    }, {'$set': {
        'sso': 'google',
    }})

    if not response['updatedExisting']:
        settings_collection.update({
            '_id': 'app',
        }, {'$set': {
            'sso': None,
        }})
