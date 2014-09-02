from constants import *
from exceptions import *
from descriptors import *
from pritunl import app_server
from mongo_object import MongoObject
from mongo_transaction import MongoTransaction
from vpn_ipv4_network import VpnIPv4Network
from cache import cache_db
import mongo
import bson
import logging
import pymongo
import ipaddress
import collections

logger = logging.getLogger(APP_NAME)

class ServerIpPool:
    def __init__(self, server):
        self.server = server

    @static_property
    def collection(cls):
        return mongo.get_collection('servers_ip_pool')

    @static_property
    def users_collection(cls):
        return mongo.get_collection('users')

    def assign_ip_addr(self, org_id, user_id):
        network = self.server.network
        server_id = self.server.id

        response = self.collection.update({
            'network': network,
            'server_id': server_id,
            'org_id': {'$exists': False},
            'user_id': {'$exists': False},
        }, {'$set': {
            'org_id': org_id,
            'user_id': user_id,
        }})
        if response.get('updatedExisting'):
            return

        ip_pool = VpnIPv4Network(network).iterhost_sets()

        try:
            doc = self.collection.find({
                'server_id': server_id,
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
                    'network': network,
                    'server_id': server_id,
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
            'network': self.server.network,
            'org_id': org_id,
            'user_id': user_id,
        }, {'$unset': {
            'org_id': '',
            'user_id': '',
        }})

    def assign_ip_pool(self, network):
        server_id = self.server.id
        pool_end = False

        ip_pool = VpnIPv4Network(network).iterhost_sets()
        bulk = self.collection.initialize_unordered_bulk_op()
        bulk_empty = True

        for org in self.server.iter_orgs():
            org_id = org.id

            for user in org.iter_users():
                try:
                    remote_ip_addr, local_ip_addr = ip_pool.next()
                except StopIteration:
                    pool_end = True
                    break
                doc_id = int(remote_ip_addr)

                bulk.find({
                    '_id': doc_id,
                }).upsert().update({'$set': {
                    '_id': doc_id,
                    'network': network,
                    'server_id': server_id,
                    'org_id': org_id,
                    'user_id': user.id,
                    'remote_addr': str(remote_ip_addr),
                    'local_addr': str(local_ip_addr),
                }})
                bulk_empty = False

            if pool_end:
                break

        if not bulk_empty:
            bulk.execute()

    def sync_ip_pool(self):
        bulk = self.collection.initialize_unordered_bulk_op()
        bulk_empty = True

        dup_user_ips = self.collection.aggregate([
            {'$match': {
                'server_id': self.server.id,
            }},
            {'$project': {
                'user_id': 1,
            }},
            {'$group': {
                '_id': {
                    'user_id': '$user_id',
                },
                'ids': {'$addToSet': '$_id'},
                'count': {'$sum': 1},
            }},
            {'$match': {
                'count': {'$gt': 1},
            }},
        ])
        for dup_user_ip in dup_user_ips['result']:
            for doc_id in dup_user_ip['ids'][1:]:
                bulk.find({
                    '_id': doc_id,
                }).update({'$unset': {
                    'org_id': '',
                    'user_id': '',
                }})
                bulk_empty = False

        if not bulk_empty:
            bulk.execute()

    def get_ip_addr(self, org_id, user_id):
        doc = self.collection.find_one({
            'server_id': self.server.id,
            'org_id': org_id,
            'user_id': user_id,
        }, {
            'local_addr': True,
            'remote_addr': True,
        })
        if doc:
            return doc['local_addr'], doc['remote_addr']
        return None, None

    @classmethod
    def multi_get_ip_addr(cls, org_id, user_ids):
        ip_addrs = collections.defaultdict(lambda: {})
        spec = {
            'org_id': org_id,
            'user_id': {'$in': user_ids},
        }
        proj = {
            'user_id': True,
            'server_id': True,
            'local_addr': True,
            'remote_addr': True,
        }

        for doc in cls.collection.find(spec, proj):
            yield doc['user_id'], doc['server_id'], \
                doc['local_addr'], doc['remote_addr']
