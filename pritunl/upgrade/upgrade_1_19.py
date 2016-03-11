from pritunl.upgrade.utils import get_collection
from pritunl import settings

def upgrade_1_19():
    settings_collection = get_collection('settings')

    settings_collection.update({
        '_id': 'app',
    }, {'$set': {
        'ssl': settings.conf.ssl,
        'port': settings.conf.port,
    }}, upsert=True)
