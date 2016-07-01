from pritunl.upgrade.utils import get_collection

from pritunl.constants import *

def upgrade_1_24():
    settings_collection = get_collection('settings')

    doc = settings_collection.find_one({'_id': 'app'})
    if doc:
        sso = doc.get('sso')
        sso_host = doc.get('sso_host')
        sso_token = doc.get('sso_token')
        sso_secret = doc.get('sso_secret')

        if sso:
            if DUO_AUTH in sso and \
                    not doc.get('sso_duo_host') and \
                    not doc.get('sso_duo_token') and \
                    not doc.get('sso_duo_secret'):
                settings_collection.update({
                    '_id': 'app',
                }, {'$set': {
                    'sso_duo_host': sso_host,
                    'sso_duo_token': sso_token,
                    'sso_duo_secret': sso_secret,
                }})
            elif sso == RADIUS_AUTH and \
                    not doc.get('sso_radius_host') and \
                    not doc.get('sso_radius_secret'):
                settings_collection.update({
                    '_id': 'app',
                }, {'$set': {
                    'sso_radius_host': sso_host,
                    'sso_radius_secret': sso_secret,
                }})
