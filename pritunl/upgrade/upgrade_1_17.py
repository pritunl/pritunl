from pritunl.upgrade.utils import get_collection

def upgrade_1_17():
    hosts_collection = get_collection('hosts')
    hosts_collection.update_many({}, {'$set': {
        'local_address': None,
    }})
