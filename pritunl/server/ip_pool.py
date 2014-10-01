from pritunl.constants import *
from pritunl.exceptions import *
from pritunl.descriptors import *
from pritunl.vpn_ipv4_network import VpnIPv4Network
from pritunl.cache import cache_db
from pritunl.app_server import app_server
from pritunl import mongo
import pritunl.ipaddress as ipaddress
import bson
import logging
import pymongo
import collections

logger = logging.getLogger(APP_NAME)

class ServerIpPool:
    def __init__(self, server):
        self.server = server

    @cached_static_property
    def collection(cls):
        return mongo.get_collection('servers_ip_pool')

    @cached_static_property
    def users_collection(cls):
        return mongo.get_collection('users')

    def assign_ip_addr(self, org_id, user_id):
        network = self.server.network
        server_id = self.server.id

        response = self.collection.update({
            'network': network,
            'server_id': server_id,
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
            'user_id': user_id,
        }, {'$unset': {
            'org_id': '',
            'user_id': '',
        }})

    def assign_ip_pool(self, network):
        server_id = self.server.id
        pool_end = False

        ip_pool = VpnIPv4Network(network).iterhost_sets()

        if mongo.has_bulk:
            bulk = self.collection.initialize_unordered_bulk_op()
            bulk_empty = True
        else:
            bulk = None
            bulk_empty = None

        for org in self.server.iter_orgs():
            org_id = org.id

            for user in org.iter_users():
                try:
                    remote_ip_addr, local_ip_addr = ip_pool.next()
                except StopIteration:
                    pool_end = True
                    break
                doc_id = int(remote_ip_addr)

                spec = {
                    '_id': doc_id,
                }
                doc = {'$set': {
                    '_id': doc_id,
                    'network': network,
                    'server_id': server_id,
                    'org_id': org_id,
                    'user_id': user.id,
                    'remote_addr': str(remote_ip_addr),
                    'local_addr': str(local_ip_addr),
                }}

                if bulk:
                    bulk.find(spec).upsert().update(doc)
                    bulk_empty = False
                else:
                    self.collection.update(spec, doc, upsert=True)

            if pool_end:
                break

        if bulk and not bulk_empty:
            bulk.execute()

    def sync_ip_pool(self):
        server_id = self.server.id

        if mongo.has_bulk:
            bulk = self.collection.initialize_unordered_bulk_op()
        else:
            bulk = None

        spec = {
            'server_id': server_id,
            'network': {'$ne': self.server.network},
        }
        if bulk:
            bulk.find(spec).remove()
        else:
            self.collection.remove(spec)

        dup_user_ips = self.collection.aggregate([
            {'$match': {
                'server_id': server_id,
                'user_id': {'$exists': True},
            }},
            {'$project': {
                'user_id': True,
            }},
            {'$group': {
                '_id': '$user_id',
                'ids': {'$addToSet': '$_id'},
                'count': {'$sum': 1},
            }},
            {'$match': {
                'count': {'$gt': 1},
            }},
        ])
        for dup_user_ip in dup_user_ips['result']:
            for doc_id in dup_user_ip['ids'][1:]:
                spec = {
                    '_id': doc_id,
                }
                doc = {'$unset': {
                    'org_id': '',
                    'user_id': '',
                }}

                if bulk:
                    bulk.find(spec).update(doc)
                else:
                    self.collection.update(spec, doc)

        user_ids = self.users_collection.find({
            'org_id': {'$in': self.server.organizations},
            'type': CERT_CLIENT,
        }, {
            'user_id': True,
        }).distinct('_id')
        user_ids = set([str(x) for x in user_ids])

        user_ip_ids = self.collection.find({
            'server_id': server_id,
        }, {
            'user_id': True,
        }).distinct('user_id')
        user_ip_ids = set(user_ip_ids)

        for user_id in user_ip_ids - user_ids:
            spec = {
                'server_id': server_id,
                'network': self.server.network,
                'user_id': user_id,
            }
            doc = {'$unset': {
                'org_id': '',
                'user_id': '',
            }}

            if bulk:
                bulk.find(spec).update(doc)
            else:
                self.collection.update(spec, doc)

        if bulk:
            bulk.execute()

        for user_id in user_ids - user_ip_ids:
            doc = self.users_collection.find_one(bson.ObjectId(user_id), {
                'org_id': True,
            })
            if doc:
                self.assign_ip_addr(doc['org_id'], user_id)

    def get_ip_addr(self, org_id, user_id):
        doc = self.collection.find_one({
            'server_id': self.server.id,
            'network': self.server.network,
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
        spec = {
            'user_id': {'$in': user_ids},
        }
        project = {
            '_id': False,
            'user_id': True,
            'server_id': True,
            'local_addr': True,
            'remote_addr': True,
        }

        for doc in cls.collection.find(spec, project):
            yield doc['user_id'], doc['server_id'], \
                doc['local_addr'], doc['remote_addr']
