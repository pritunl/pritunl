from pritunl.upgrade.utils import get_collection

def upgrade_1_18():
    servers_collection = get_collection('servers')
    settings_collection = get_collection('settings')

    nat = True
    doc = settings_collection.find_one({'_id': 'vpn'})
    if doc:
        nat = doc.get('nat_routes', True)

    for doc in servers_collection.find({}):
        routes = []

        if doc.get('mode') == 'all_traffic':
            routes.append({
                'network': '0.0.0.0/0',
                'nat': nat,
            })

        for local_network in doc.get('local_networks', []):
            routes.append({
                'network': local_network,
                'nat': nat,
            })

        servers_collection.update({
            '_id': doc['_id'],
        }, {'$set': {
            'routes': routes,
        }})
