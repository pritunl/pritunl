from constants import *
from exceptions import *
from descriptors import *
from pritunl import app_server
from mongo_object import MongoObject
from cache import cache_db
import mongo
import ipaddress

logger = logging.getLogger(APP_NAME)

class ServerIpPool:
    def __init__(self, server):
        self.server = server

    @static_property
    def collection(cls):
        return mongo.get_collection('servers_ip_pool')

    def assign_ip_addr(self, org_id, user_id):
        response = servers_ip_pool_db.update({
            'server_id': self.server.id,
            'org_id': {'$exists': False},
            'user_id': {'$exists': False},
        }, {'$set': {
            'org_id': org_id,
            'user_id': user_id,
        }})
        if response.get('updatedExisting'):
            return

        ip_pool = ipaddress.IPv4Network(network).iterhosts()
        ip_pool.next()

        try:
            doc = servers_ip_pool_db.find({
                'server_id': self.server.id,
            }).sort('_id', pymongo.DESCENDING)[0]
            if doc:
                last_addr = doc['_id']
                for addr in ip_pool:
                    if int(addr) == last_addr:
                        break
        except IndexError:
            pass

        try:
            while True:
                remote_ip_addr = ip_pool.next()
                ip_addr_endpoint = str(remote_ip_addr).split('.')[-1]
                if ip_addr_endpoint not in VALID_IP_ENDPOINTS:
                    continue
                local_ip_addr = ip_pool.next()

                try:
                    servers_ip_pool_db.insert({
                        '_id': int(remote_ip_addr),
                        'server_id': self.server.id,
                        'org_id': org_id,
                        'user_id': user_id,
                        'remote_addr': str(remote_ip_addr),
                        'local_addr': str(local_ip_addr),
                    })
                    break
                except pymongo.errors.DuplicateKeyError:
                    pass
        except StopIteration:
            pass

    def unassign_ip_addr(self, org_id, user_id):
        servers_ip_pool_db.update({
            'server_id': self.server.id,
            'org_id': org_id,
            'user_id': user_id,
        }, {'$unset': {
            'org_id': '',
            'user_id': '',
        }})
