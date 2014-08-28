from constants import *
from exceptions import *
from descriptors import *
from pritunl import app_server
from mongo_object import MongoObject
from vpn_ipv4_network import VpnIPv4Network
from cache import cache_db
import mongo

logger = logging.getLogger(APP_NAME)

class ServerIpPool:
    def __init__(self, server):
        self.server = server

    @static_property
    def collection(cls):
        return mongo.get_collection('servers_ip_pool')

    def assign_ip_addr(self, org_id, user_id):
        response = self.collection.update({
            'server_id': self.server.id,
            'org_id': {'$exists': False},
            'user_id': {'$exists': False},
        }, {'$set': {
            'org_id': org_id,
            'user_id': user_id,
        }})
        if response.get('updatedExisting'):
            return

        ip_pool = VpnIPv4Network(self.server.network)

        try:
            doc = self.collection.find({
                'server_id': self.server.id,
            }).sort('_id', pymongo.DESCENDING)[0]
            if doc:
                last_addr = doc['_id']
                for remote_ip_addr, local_ip_addr in ip_pool:
                    if int(remote_ip_addr) == last_addr:
                        break
        except IndexError:
            pass

        for remote_ip_addr, local_ip_addr in ip_pool:
            try:
                self.collection.insert({
                    '_id': int(remote_ip_addr),
                    'server_id': self.server.id,
                    'org_id': org_id,
                    'user_id': user_id,
                    'remote_addr': str(remote_ip_addr),
                    'local_addr': str(remote_ip_addr),
                })
                break
            except pymongo.errors.DuplicateKeyError:
                pass

    def unassign_ip_addr(self, org_id, user_id):
        self.collection.update({
            'server_id': self.server.id,
            'org_id': org_id,
            'user_id': user_id,
        }, {'$unset': {
            'org_id': '',
            'user_id': '',
        }})

    def get_ip_addr(self, org_id, user_id):
        doc = self.collection.find_one({
            'server_id': self.server.id,
            'org_id': org_id,
            'user_id': user_id,
        })
        if doc:
            return ipaddress.IPv4Address(doc['remote_addr']), \
                ipaddress.IPv4Address(doc['local_addr'])
        return None, None
