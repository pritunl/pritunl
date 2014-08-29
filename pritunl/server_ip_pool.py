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

logger = logging.getLogger(APP_NAME)

class ServerIpPool:
    def __init__(self, server):
        self.server = server

    @static_property
    def collection(cls):
        return mongo.get_collection('servers_ip_pool')

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

    def assign_ip_pool(self, old_network=None):
        network = self.server.network
        server_id = self.server.id
        pool_end = False

        tran = MongoTransaction()
        ip_pool = VpnIPv4Network(network).iterhost_sets()

        for org in self.server.iter_orgs():
            org_id = org.id

            for user in org.iter_users():
                try:
                    remote_ip_addr, local_ip_addr = ip_pool.next()
                except StopIteration:
                    pool_end = True
                    break
                doc_id = int(remote_ip_addr)

                tran.servers_ip_pool_collection.bulk().find({
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

            if pool_end:
                break

        tran.servers_ip_pool_collection.bulk_execute()

        tran.servers_ip_pool_collection.rollback().remove({
            'server_id': server_id,
        })

        tran.servers_ip_pool_collection.rollback().update({
            '_id': bson.ObjectId(server_id),
        }, {'$set': {
            'network_lock': False,
        }})

        if old_network:
            tran.servers_ip_pool_collection.post().remove({
                'network': old_network,
                'server_id': server_id,
            })

        tran.servers_collection.post().update({
            '_id': bson.ObjectId(server_id),
        }, {'$set': {
            'network_lock': False,
        }})

        tran.commit()

    def get_ip_addr(self, org_id, user_id):
        doc = self.collection.find_one({
            'server_id': self.server.id,
            'org_id': org_id,
            'user_id': user_id,
        })
        if doc:
            return str(ipaddress.IPv4Address(doc['local_addr'])), \
                str(ipaddress.IPv4Address(doc['remote_addr']))
        return None, None
